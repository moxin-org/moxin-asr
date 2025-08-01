import copy
import time
import unicodedata
from queue import Queue, Empty

from langchain.memory import ConversationBufferWindowMemory
from langchain_core.chat_history import InMemoryChatMessageHistory

from voice_dialogue.config.llm_config import get_llm_model_params, get_apple_silicon_summary, BUILTIN_LLM_MODEL_PATH
from voice_dialogue.config.user_config import get_prompt
from voice_dialogue.core.base import BaseThread
from voice_dialogue.core.constants import chat_history_cache
from voice_dialogue.llm.processor import (
    preprocess_sentence_text, create_langchain_chat_llamacpp_instance,
    create_langchain_pipeline, warmup_langchain_pipeline
)
from voice_dialogue.models.voice_task import VoiceTask, QuestionDisplayMessage
from voice_dialogue.services.mixins import TaskStatusMixin
from voice_dialogue.utils.logger import logger


class LLMService(BaseThread, TaskStatusMixin):
    """LLM 回答生成器 - 负责使用语言模型生成回答文本"""

    def __init__(
            self, group=None, target=None, name=None, args=(), kwargs={}, *, daemon=None,
            user_question_queue: Queue,
            generated_answer_queue: Queue,
            websocket_message_queue: Queue = None
    ):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)

        self.user_question_queue = user_question_queue
        self.generated_answer_queue = generated_answer_queue
        self.websocket_message_queue = websocket_message_queue

        self.english_sentence_end_marks = {'!', '?', '.', ',', ':', ';'}
        self.chinese_sentence_end_marks = {'，', '。', '！', '？', '：', '；', '、'}
        self.sentence_end_marks = self.english_sentence_end_marks | self.chinese_sentence_end_marks

    def _get_prompt_by_language(self, language: str) -> str:
        """根据语言获取对应的 prompt"""
        return get_prompt(language)

    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        message_history = InMemoryChatMessageHistory()
        if session_id not in chat_history_cache:
            return message_history

        for k, message in chat_history_cache.get(session_id).items():
            identity = k.rsplit(':')[-1]
            if identity == 'human':
                message_history.add_user_message(message)
            elif identity == 'ai':
                message_history.add_ai_message(' '.join(message))

        memory = ConversationBufferWindowMemory(
            chat_memory=message_history,
            k=3,
            return_messages=True,
        )
        assert len(memory.memory_variables) == 1
        key = memory.memory_variables[0]
        messages = memory.load_memory_variables({})[key]
        return InMemoryChatMessageHistory(messages=messages)

    def _should_end_sentence(self, sentence: str, sentence_end_mark: str, is_first_sentence: bool) -> bool:
        """判断是否应该结束当前句子"""
        if not sentence or sentence_end_mark not in self.sentence_end_marks:
            return False

        is_chinese_sentence = False
        if sentence_end_mark in self.chinese_sentence_end_marks:
            is_chinese_sentence = True

        # 第一个句子的特殊处理逻辑
        if is_first_sentence:
            if is_chinese_sentence:
                return (len(sentence) > 2 and sentence_end_mark in self.chinese_sentence_end_marks)
            else:
                return (len(sentence.split()) > 1 and sentence_end_mark in self.english_sentence_end_marks)

        # 普通句子的判断逻辑
        if is_chinese_sentence:
            sentence_words = len(sentence)
            return sentence_words > 4
        else:
            sentence_words = len(sentence.split())
            return sentence_words > 4 or (sentence_words > 2 and sentence_end_mark in {'.', '?', '!', })

    def _send_sentence_to_queue(self, voice_task: VoiceTask, sentence: str, answer_index: int) -> None:
        """将句子发送到队列"""
        voice_task.answer_index = answer_index
        voice_task.answer_sentence = sentence.strip()
        voice_task.llm_end_time = time.time()
        self.generated_answer_queue.put(copy.deepcopy(voice_task))
        voice_task.llm_start_time = time.time()

    def _reset_chunks(self, remain_content: str) -> list:
        """重置 chunks 列表"""
        return [remain_content] if remain_content else []

    def _is_punctuation(self, char: str) -> bool:
        """判断一个字符是否是标点符号"""
        if not char or len(char) != 1:
            return False
        # 检查字符的 Unicode 类别是否为标点符号 (Punctuation)
        return unicodedata.category(char).startswith('P')

    def _process_chunk_content(self, chunk_content: str) -> tuple:
        """处理 chunk 内容，从右到左找标点符号并分割成三部分"""
        if not chunk_content:
            return '', '', ''

        # 从右到左迭代，找到第一个标点符号
        for i in range(len(chunk_content) - 1, -1, -1):
            char = chunk_content[i]
            if self._is_punctuation(char):
                # 找到标点符号，分割成三部分
                before_punct = chunk_content[:i]  # 标点之前的部分
                punct = char  # 标点符号本身
                after_punct = chunk_content[i + 1:]  # 标点之后的部分
                return before_punct, punct, after_punct

        # 如果没有找到标点符号，返回整个内容作为第一部分
        return chunk_content, '', ''

    def _process_voice_task(self, voice_task: VoiceTask) -> None:
        """处理单个语音任务"""

        chunks = []
        answer_index = 0
        is_first_sentence = True

        user_question = voice_task.transcribed_text
        logger.info(f'用户问题: {user_question}')
        if self.websocket_message_queue:
            self.websocket_message_queue.put_nowait(
                QuestionDisplayMessage(
                    session_id=voice_task.session_id,
                    question=user_question,
                    task_id=voice_task.id,
                )
            )

        voice_task.llm_start_time = time.time()

        system_prompt = self._get_prompt_by_language(voice_task.language)
        pipeline = create_langchain_pipeline(self.model_instance, system_prompt, self.get_session_history)

        config = {"configurable": {"session_id": voice_task.session_id}}

        try:
            for chunk in pipeline.stream(input={'input': user_question}, config=config):

                if not self.is_task_valid(voice_task):
                    return

                if not chunk.content:
                    continue
                elif chunk.content in {'<think>', '\n\n', '</think>'}:
                    continue

                chunk_content = f'{chunk.content}'

                before_punct, sentence_end_mark, remain_content = self._process_chunk_content(chunk_content)
                if before_punct:
                    chunks.append(before_punct)
                if sentence_end_mark:
                    chunks.append(sentence_end_mark)

                sentence = preprocess_sentence_text(chunks)
                if not sentence:
                    chunks.append(remain_content)
                    continue

                # 检查是否应该结束当前句子
                if self._should_end_sentence(sentence, sentence_end_mark, is_first_sentence):
                    self._send_sentence_to_queue(voice_task, sentence, answer_index)
                    chunks = self._reset_chunks(remain_content)
                    answer_index += 1
                    is_first_sentence = False
                else:
                    if remain_content:
                        chunks.append(remain_content)

            # 处理最后剩余的 chunks
            self._handle_remaining_chunks(voice_task, chunks, answer_index)

        except Exception as e:
            logger.error(f'处理语音任务时发生错误: {e}')

    def _handle_remaining_chunks(self, voice_task: VoiceTask, chunks: list, answer_index: int) -> None:
        """处理剩余的 chunks"""
        if not chunks:
            return

        sentence = preprocess_sentence_text(chunks)
        if not sentence or sentence.strip() in self.sentence_end_marks:
            return

        self._send_sentence_to_queue(voice_task, sentence, answer_index)

    def run(self):

        model_params = get_llm_model_params()

        # 打印芯片信息和优化配置
        chip_summary = get_apple_silicon_summary()
        logger.info(f"检测到芯片: {chip_summary['chip_name']}")
        logger.info(f"性能核心数: {chip_summary['performance_cores']}")
        logger.info(f"使用线程数: {chip_summary['optimal_n_threads']} (仅使用性能核心)")
        logger.info(f"上下文窗口: {chip_summary['optimal_n_ctx']}")
        logger.info(f"配置说明: {chip_summary['config_note']}")

        self.model_instance = create_langchain_chat_llamacpp_instance(
            local_model_path=BUILTIN_LLM_MODEL_PATH, model_params=model_params
        )
        # 使用默认中文 prompt 进行 warmup
        prompt = get_prompt("zh")
        pipeline = create_langchain_pipeline(self.model_instance, prompt, self.get_session_history)
        warmup_langchain_pipeline(pipeline)

        self.is_ready = True

        """主运行循环"""
        while not self.is_exited:
            try:
                voice_task: VoiceTask = self.user_question_queue.get(block=True, timeout=1)
                self._process_voice_task(voice_task)
            except Empty:
                continue
            except Exception as e:
                logger.error(f'AnswerGeneratorWorker 运行时发生错误: {e}')
