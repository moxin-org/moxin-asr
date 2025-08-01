import sys
import unittest
from pathlib import Path

from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_community.chat_models.llamacpp import ChatLlamaCpp
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

HERE = Path(__file__).parent.parent
lib_path = HERE / "src"
if lib_path.exists() and lib_path.as_posix() not in sys.path:
    sys.path.insert(0, lib_path.as_posix())

from voice_dialogue.config.llm_config import get_llm_model_params, BUILTIN_LLM_MODEL_PATH
from voice_dialogue.llm.processor import create_langchain_pipeline

CHINESE_SYSTEM_PROMPT = (
    "你是AI助手。请以自然流畅的中文口语化表达直接回答问题，避免冗余的思考过程。"
    "你的回答第一句话必须少于十个字。每段回答控制在二到三句话，既不要过短也不要过长，以适应对话语境。"
    "回答应准确、精炼且有依据。"
    "/no_think"
)

ENGLISH_SYSTEM_PROMPT = (
    "You are an AI assistant. "
    "Please answer directly and naturally, using conversational English, without showing your thinking process. "
    "Your first sentence must be less than 10 words. "
    "Your responses should be accurate, concise, and well-supported, ideally around 2-3 sentences long to ensure a good conversational flow."
    "/no_think"
)

if not CHINESE_SYSTEM_PROMPT:
    from voice_dialogue.config.llm_config import CHINESE_SYSTEM_PROMPT

if not ENGLISH_SYSTEM_PROMPT:
    from voice_dialogue.config.llm_config import ENGLISH_SYSTEM_PROMPT


class TestLLMDialogue(unittest.TestCase):

    def setUp(self):
        model_params = get_llm_model_params()
        self.history_store = {}

        self.langchain_instance = ChatLlamaCpp(model_path=BUILTIN_LLM_MODEL_PATH.as_posix(), **model_params)

        pipeline = create_langchain_pipeline(
            self.langchain_instance,
            self._get_prompt_by_language('zh'),
            self.get_session_history
        )
        self.warmup(pipeline)

        self.test_datasets = [
            {
                'session_id': 'test_dataset_1',
                'language': 'zh',
                'questions': [
                    # 第1轮：开放性话题引入
                    "最近人工智能技术发展很快，你觉得AI对我们日常生活带来了哪些改变？",
                    # 第2轮：基于前一个回答的深入探讨
                    "你刚才提到的这些改变中，哪一个你认为是最重要的？为什么？",
                    # 第3轮：转向具体场景和个人观点
                    "如果让你选择一个AI应用来帮助解决教育领域的问题，你会选择什么？具体怎么实现？",
                    # 第4轮：挑战性问题，测试逻辑思维
                    "但是也有人担心AI在教育中会让学生过度依赖技术，失去独立思考能力。你怎么看待这个担忧？",
                    # 第5轮：总结性问题，测试整合能力
                    "综合我们刚才讨论的内容，你认为在AI快速发展的时代，普通人应该如何适应和准备？"
                ]
            },
            {
                'session_id': 'test_dataset_2',
                'language': 'zh',
                'questions': [
                    # 第1轮：开放性话题引入
                    "近年来环境问题越来越受到关注，你认为我们个人在日常生活中可以为环保做些什么？",
                    # 第2轮：基于前一个回答的深入探讨
                    "在这些环保行为中，你觉得哪一种最容易被大家接受和实践？原因是什么？",
                    # 第3rd轮：转向具体场景和个人观点
                    "如果让你设计一个推广垃圾分类的社区活动，你会怎么做？",
                    # 第4轮：挑战性问题，测试逻辑思维
                    "有些人认为，个人的环保努力相比工业污染只是杯水车薪，这种看法你怎么看？",
                    # 第5轮：总结性问题，测试整合能力
                    "总的来说，为了实现可持续发展，你认为政府、企业和个人应该分别扮演什么样的角色？"
                ]
            },
            {
                'session_id': 'test_dataset_3',
                'language': 'zh',
                'questions': [
                    # 第1轮：开放性话题引入
                    "随着科技的发展，未来的工作模式可能会发生很大变化，你想象中未来的工作是什么样的？",
                    # 第2轮：基于前一个回答的深入探讨
                    "你提到的远程办公和灵活工作时间，对员工和公司来说，各自最大的好处和挑战是什么？",
                    # 第3轮：转向具体场景和个人观点
                    "假设你是一名公司经理，你会如何利用技术工具来提高远程团队的协作效率？",
                    # 第4轮：挑战性问题，测试逻辑思维
                    "自动化和人工智能可能会取代一部分人的工作，这引起了很多人的焦虑。你认为我们应该如何应对这种“失业恐慌”？",
                    # 第5轮：总结性问题，测试整合能力
                    "面对未来工作的种种不确定性，你认为现在的年轻人最需要培养哪些核心能力？"
                ]
            },
            {
                'session_id': 'test_dataset_4',
                'language': 'en',
                'questions': [
                    # Round 1: Open-ended topic introduction
                    "Mental health has become a more prominent topic recently. What are some common stressors you think people face in modern society?",
                    # Round 2: In-depth discussion based on the previous answer
                    "Of the stressors you mentioned, which one do you believe has the most significant impact on people's well-being, and why?",
                    # Round 3: Shift to specific scenarios and personal opinions
                    "If you were to design a mobile app to help people manage stress, what key features would you include?",
                    # Round 4: Challenging question, testing logical thinking
                    "Some argue that the increased focus on mental health can sometimes lead to over-diagnosis or the medicalization of normal emotions. What are your thoughts on this concern?",
                    # Round 5: Summarizing question, testing integration ability
                    "To sum up, what kind of societal changes do you think would be most effective in promoting better mental health for everyone?"
                ]
            },
            {
                'session_id': 'test_dataset_5',
                'language': 'en',
                'questions': [
                    # Round 1: Open-ended topic introduction
                    "Humanity has always been fascinated by space. What do you see as the most exciting developments in space exploration right now?",
                    # Round 2: In-depth discussion based on the previous answer
                    "You mentioned the push towards colonizing Mars. What do you think are the biggest scientific and ethical challenges we need to overcome for that to become a reality?",
                    # Round 3: Shift to specific scenarios and personal opinions
                    "If you were given the chance to send a single message to an extraterrestrial civilization, what would it say?",
                    # Round 4: Challenging question, testing logical thinking
                    "There's a debate about whether the vast amounts of money spent on space exploration could be better used to solve problems here on Earth. How would you justify the continued investment in space programs?",
                    # Round 5: Summarizing question, testing integration ability
                    "Considering everything we've discussed, what long-term benefits do you believe humanity will gain from its ventures into space?"
                ]
            }
        ]

    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self.history_store:
            message_history = InMemoryChatMessageHistory()
            self.history_store[session_id] = message_history
            return self.history_store[session_id]

        memory = ConversationBufferWindowMemory(
            chat_memory=self.history_store[session_id],
            k=3,
            return_messages=True,
        )
        assert len(memory.memory_variables) == 1
        key = memory.memory_variables[0]
        messages = memory.load_memory_variables({})[key]
        self.history_store[session_id] = InMemoryChatMessageHistory(messages=messages)
        return self.history_store[session_id]

    def warmup(self, pipeline: RunnableWithMessageHistory = None):
        session_id = 'warmup'
        config = {"configurable": {"session_id": session_id}}
        for chunk in pipeline.stream(input={'input': 'This is a warmup step.'}, config=config):
            pass

    def _get_prompt_by_language(self, language: str) -> str:
        """根据语言获取对应的 prompt"""
        if language == "zh":
            return CHINESE_SYSTEM_PROMPT
        else:
            return ENGLISH_SYSTEM_PROMPT

    def test_dialogue(self):
        for test_dataset in self.test_datasets:
            session_id = test_dataset.get('session_id')
            language = test_dataset.get('language')
            questions = test_dataset.get('questions')

            # --- Test Suite Header ---
            print("\n" + "=" * 80)
            print(f"  🧪 EXECUTING TEST SUITE: {session_id} ({language.upper()})")
            print("=" * 80)

            # --- Langchain Pipeline Setup ---
            prompt = self._get_prompt_by_language(language)
            pipeline = create_langchain_pipeline(self.langchain_instance, prompt, self.get_session_history)
            config = {"configurable": {"session_id": session_id}}

            for i, question in enumerate(questions):
                round_num = i + 1
                print(f"\n🗣️  Round {round_num}")
                print(f"  👤 User: {question}")
                print(f"  🤖 AI:   ", end='')

                # --- Stream and print LLM response ---
                for chunk in pipeline.stream(input={'input': question}, config=config):
                    print(chunk.content, end='', flush=True)

                print("\n" + "-" * 80)

            # --- Test Suite Footer ---
            print(f"\n✅ TEST SUITE COMPLETED: {session_id}")
            print("=" * 80 + "\n")
