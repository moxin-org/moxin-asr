import time
import unittest
from pathlib import Path

import soundfile

from voice_dialogue.services.audio.generators import tts_config_registry
from voice_dialogue.services.audio.generators.manager import tts_manager
from voice_dialogue.utils.logger import logger


class TestTTSAudioGenerator(unittest.TestCase):
    """
    TTS音频生成器单元测试
    
    测试目标：
    1. 根据语言使用不同的测试文本
    2. 每个音色使用多个不同长度的文本进行生成
    3. 记录每次生成的时间
    """

    def setUp(self):
        """初始化测试环境"""
        self.test_results = []
        here = Path(__file__).parent
        self.output_dir = here / "tts_test_output"
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        # 可选：清理生成的音频文件
        # import shutil
        # shutil.rmtree(self.output_dir, ignore_errors=True)
        pass

    def get_test_texts_by_language(self, is_chinese: bool):
        """根据语言获取测试文本"""
        if is_chinese:
            return {
                "short": [
                    "你好。",
                    "谢谢。",
                    "再见。",
                    "很高兴见到你。",
                    "今天天气不错。"
                ],
                "medium": [
                    "人工智能是一门研究计算机系统如何模拟人类智能的学科。",
                    "我们正处在一个科技飞速发展的时代，各种新技术层出不穷。",
                    "学习新知识需要持之以恒的努力和坚定的决心。",
                    "在这个信息爆炸的时代，学会筛选有价值的信息变得越来越重要。",
                    "科技的进步为人类带来了便利，同时也带来了新的挑战和思考。"
                ],
                "long": [
                    "随着人工智能技术的不断发展，我们的生活正在发生着深刻的变化。从智能手机到自动驾驶汽车，从语音助手到智能家居，人工智能已经渗透到我们生活的方方面面。然而，在享受科技便利的同时，我们也需要思考如何在人工智能时代保持人类的独特价值和创造力。",
                    "教育是人类文明传承的重要途径，也是社会进步的基石。在新时代背景下，教育面临着前所未有的机遇和挑战。我们需要培养学生的创新思维和实践能力，让他们具备适应未来社会发展的综合素质。同时，教育工作者也需要不断学习和成长，以更好地引导学生成长。",
                    "环境保护是全人类共同面临的重要课题。气候变化、空气污染、水资源短缺等问题日益严重，需要我们每个人都行动起来。从日常生活的点点滴滴做起，比如节约用水用电、垃圾分类、绿色出行等，虽然看似微小，但汇聚起来就是巨大的力量。让我们携手共建美丽地球家园。"
                ]
            }
        else:
            return {
                "short": [
                    "Hello.",
                    "Thank you.",
                    "Goodbye.",
                    "Nice to meet you.",
                    "Have a great day."
                ],
                "medium": [
                    "Artificial intelligence is transforming the way we live and work in unprecedented ways.",
                    "Technology has become an integral part of our daily lives, connecting people across the globe.",
                    "Learning new skills requires dedication, patience, and a willingness to embrace challenges.",
                    "In our interconnected world, effective communication is more important than ever before.",
                    "Innovation drives progress and creates opportunities for future generations to thrive."
                ],
                "long": [
                    "The rapid advancement of technology has revolutionized virtually every aspect of human society. From healthcare and education to transportation and entertainment, digital innovations continue to reshape our world at an unprecedented pace. As we navigate this technological revolution, it's crucial to maintain a balance between embracing progress and preserving human values that define our humanity.",
                    "Climate change represents one of the most pressing challenges of our time, requiring immediate and coordinated global action. The scientific consensus is clear: human activities are contributing to rising temperatures, extreme weather events, and ecosystem disruption. However, there is still hope if we act decisively to reduce carbon emissions, invest in renewable energy, and adopt sustainable practices in all sectors of society.",
                    "Education in the 21st century must evolve to prepare students for a rapidly changing world. Traditional teaching methods are being enhanced with digital tools, personalized learning approaches, and interdisciplinary curricula. Students need to develop not only academic knowledge but also critical thinking skills, creativity, emotional intelligence, and adaptability to succeed in their future careers and contribute meaningfully to society."
                ]
            }

    def test_all_available_tts_models(self):
        """测试所有可用的TTS模型"""
        logger.info("\n" + "=" * 80)
        logger.info("  🎵 开始TTS音频生成器性能测试")
        logger.info("=" * 80)

        # 获取所有可用的TTS配置
        all_configs = tts_config_registry.get_all_configs()

        if not all_configs:
            self.skipTest("没有找到可用的TTS配置")

        logger.info(f"发现 {len(all_configs)} 个TTS配置")

        for config in all_configs:
            # 只测试模型文件完整的配置
            if not config.is_model_complete():
                logger.warning(f"跳过未完整下载的模型: {config.character_name}")
                continue

            self._test_single_tts_model(config)

        # 打印测试总结
        self._print_test_summary()

    def _test_single_tts_model(self, config):
        """测试单个TTS模型"""
        logger.info(f"\n🎤 测试音色: {config.character_name}")
        logger.info(f"   类型: {config.tts_type.value}")
        logger.info(f"   语言: {'中文' if config.is_chinese_voice else '英文'}")
        logger.info(f"   描述: {config.description}")

        try:
            # 创建TTS实例
            tts_instance = tts_manager.create_tts(config)

            # 设置和预热
            setup_start = time.time()
            tts_instance.setup()
            setup_time = time.time() - setup_start

            warmup_start = time.time()
            tts_instance.warmup()
            warmup_time = time.time() - warmup_start

            logger.info(f"   ⚙️  模型加载时间: {setup_time:.2f}s")
            logger.info(f"   🔥 预热时间: {warmup_time:.2f}s")

            # 获取测试文本
            test_texts = self.get_test_texts_by_language(config.is_chinese_voice)

            # 测试不同长度的文本
            for length_category, texts in test_texts.items():
                logger.info(f"\n   📝 测试 {length_category} 文本:")

                for i, text in enumerate(texts, 1):
                    result = self._test_single_text(
                        tts_instance,
                        config,
                        text,
                        length_category,
                        i
                    )
                    self.test_results.append(result)

        except Exception as e:
            logger.error(f"   ❌ 测试 {config.character_name} 时出错: {e}")
            error_result = {
                'character_name': config.character_name,
                'tts_type': config.tts_type.value,
                'error': str(e),
                'status': 'failed'
            }
            self.test_results.append(error_result)

    def _test_single_text(self, tts_instance, config, text, length_category, text_index):
        """测试单条文本的TTS生成"""
        text_preview = text[:30] + "..." if len(text) > 30 else text

        try:
            # 记录开始时间
            start_time = time.time()

            # 生成音频
            audio_data, sample_rate = tts_instance.synthesize(text)

            # 记录结束时间
            end_time = time.time()
            generation_time = end_time - start_time

            # 计算音频时长
            audio_duration = len(audio_data) / sample_rate

            # 计算实时率（RTF: Real Time Factor）
            rtf = generation_time / audio_duration if audio_duration > 0 else float('inf')

            # 保存音频文件
            audio_filename = self._save_audio_file(
                audio_data,
                sample_rate,
                config.character_name,
                length_category,
                text_index
            )

            logger.info(f"     {text_index}. '{text_preview}'")
            logger.info(f"        ⏱️  生成时间: {generation_time:.3f}s")
            logger.info(f"        🎵 音频时长: {audio_duration:.3f}s")
            logger.info(f"        📊 实时率RTF: {rtf:.3f}")
            logger.info(f"        💾 保存至: {audio_filename}")

            return {
                'character_name': config.character_name,
                'tts_type': config.tts_type.value,
                'is_chinese_voice': config.is_chinese_voice,
                'length_category': length_category,
                'text_index': text_index,
                'text': text,
                'text_length': len(text),
                'generation_time': generation_time,
                'audio_duration': audio_duration,
                'rtf': rtf,
                'sample_rate': sample_rate,
                'audio_filename': audio_filename,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"     ❌ 生成失败: {e}")
            return {
                'character_name': config.character_name,
                'tts_type': config.tts_type.value,
                'length_category': length_category,
                'text_index': text_index,
                'text': text,
                'error': str(e),
                'status': 'failed'
            }

    def _save_audio_file(self, audio_data, sample_rate, character_name, length_category, text_index):
        """保存音频文件"""
        # 创建音色目录
        voice_dir = self.output_dir / character_name.replace(' ', '_')
        voice_dir.mkdir(exist_ok=True)

        # 生成文件名
        filename = f"{length_category}_{text_index:02d}.wav"
        filepath = voice_dir / filename

        # 保存为WAV文件
        soundfile.write(filepath.as_posix(), audio_data, sample_rate, subtype='PCM_16')

        return str(filepath)

    def _print_test_summary(self):
        """打印测试总结"""
        logger.info("\n" + "=" * 80)
        logger.info("  📊 TTS音频生成器测试总结")
        logger.info("=" * 80)

        successful_tests = [r for r in self.test_results if r.get('status') == 'success']
        failed_tests = [r for r in self.test_results if r.get('status') == 'failed']

        logger.info(f"✅ 成功测试: {len(successful_tests)}")
        logger.info(f"❌ 失败测试: {len(failed_tests)}")
        logger.info(f"📈 总测试数: {len(self.test_results)}")

        if successful_tests:
            # 按音色分组统计
            from collections import defaultdict
            stats_by_voice = defaultdict(list)

            for result in successful_tests:
                stats_by_voice[result['character_name']].append(result)

            logger.info(f"\n🎭 各音色性能统计:")
            for character_name, results in stats_by_voice.items():
                rtf_values = [r['rtf'] for r in results]
                avg_rtf = sum(rtf_values) / len(rtf_values)
                min_rtf = min(rtf_values)
                max_rtf = max(rtf_values)

                generation_times = [r['generation_time'] for r in results]
                avg_gen_time = sum(generation_times) / len(generation_times)

                logger.info(f"  {character_name}:")
                logger.info(f"    测试数量: {len(results)}")
                logger.info(f"    平均RTF: {avg_rtf:.3f}")
                logger.info(f"    RTF范围: {min_rtf:.3f} - {max_rtf:.3f}")
                logger.info(f"    平均生成时间: {avg_gen_time:.3f}s")

        if failed_tests:
            logger.info(f"\n❌ 失败的测试:")
            for failed in failed_tests:
                logger.error(f"  {failed['character_name']}: {failed.get('error', 'Unknown error')}")

        logger.info(f"\n💾 音频文件保存在: {self.output_dir}")
        logger.info("=" * 80)

    def test_rtf_performance_benchmarks(self):
        """测试RTF性能基准"""
        logger.info("\n🏃‍♂️ 执行RTF性能基准测试...")

        # 定义性能基准
        RTF_EXCELLENT = 0.3  # 优秀
        RTF_GOOD = 0.5  # 良好
        RTF_ACCEPTABLE = 1.0  # 可接受

        successful_tests = [r for r in self.test_results if r.get('status') == 'success']

        if not successful_tests:
            self.skipTest("没有成功的测试结果用于性能基准测试")

        performance_categories = {
            'excellent': [],
            'good': [],
            'acceptable': [],
            'poor': []
        }

        for result in successful_tests:
            rtf = result['rtf']
            if rtf <= RTF_EXCELLENT:
                performance_categories['excellent'].append(result)
            elif rtf <= RTF_GOOD:
                performance_categories['good'].append(result)
            elif rtf <= RTF_ACCEPTABLE:
                performance_categories['acceptable'].append(result)
            else:
                performance_categories['poor'].append(result)

        # 打印性能分类统计
        logger.info(f"🏆 优秀 (RTF ≤ {RTF_EXCELLENT}): {len(performance_categories['excellent'])}")
        logger.info(f"✅ 良好 (RTF ≤ {RTF_GOOD}): {len(performance_categories['good'])}")
        logger.info(f"⚠️  可接受 (RTF ≤ {RTF_ACCEPTABLE}): {len(performance_categories['acceptable'])}")
        logger.info(f"❌ 较差 (RTF > {RTF_ACCEPTABLE}): {len(performance_categories['poor'])}")

        # 确保至少有一些测试达到可接受的性能
        acceptable_count = (len(performance_categories['excellent']) +
                            len(performance_categories['good']) +
                            len(performance_categories['acceptable']))

        self.assertGreater(
            acceptable_count,
            0,
            "没有TTS模型达到可接受的性能标准（RTF ≤ 1.0）"
        )


if __name__ == '__main__':
    unittest.main()
