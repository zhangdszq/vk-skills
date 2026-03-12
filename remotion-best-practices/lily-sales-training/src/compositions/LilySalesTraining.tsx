import {
	AbsoluteFill,
	useCurrentFrame,
	Sequence,
	interpolate,
} from 'remotion';
import {Cover} from '../components/Cover';
import {ChapterTitle} from '../components/ChapterTitle';
import {ContentSlide} from '../components/ContentSlide';
import {FormulaCard} from '../components/FormulaCard';
import {DialogueSlide} from '../components/DialogueSlide';

// 场景定义
const SCENES = [
	// 封面 - 90帧 (3秒)
	{
		duration: 90,
		component: Cover,
		props: {
			title: '销冠Lily的销售心法',
			subtitle: 'VIPKID绘本馆销售赋能内部手册',
		},
	},
	// 开篇 - 150帧 (5秒)
	{
		duration: 150,
		component: ChapterTitle,
		props: {
			chapterNumber: '开篇',
			title: '为什么是Lily？',
			description: '连续18个月销冠 · 101条成交记录 · 转化率高达40%',
			icon: '🏆',
		},
	},
	// 第一章标题 - 120帧 (4秒)
	{
		duration: 120,
		component: ChapterTitle,
		props: {
			chapterNumber: '第一章',
			title: '邀约篇',
			description: '如何通过电话快速建立信任并赢得面谈机会',
			icon: '📞',
		},
	},
	// 电话前准备 - 180帧 (6秒)
	{
		duration: 180,
		component: ContentSlide,
		props: {
			title: '电话前准备工作',
			points: [
				'了解孩子年龄和英语基础',
				'准备开放性问题（非是/否题）',
				'调整心态：我是来帮忙的，不是来推销的',
				'找到家长的焦虑点',
			],
			backgroundColor:
				'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
		},
	},
	// 黄金前30秒 - 180帧 (6秒)
	{
		duration: 180,
		component: ContentSlide,
		props: {
			title: '黄金前30秒',
			points: [
				'建立连接：感谢/赞美/共情',
				'表明身份：简洁有力',
				'抛出钩子：孩子英语学习的痛点',
				'申请时间：只需2分钟',
			],
			backgroundColor:
				'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
		},
	},
	// 第二章标题 - 120帧 (4秒)
	{
		duration: 120,
		component: ChapterTitle,
		props: {
			chapterNumber: '第二章',
			title: '诊脉篇',
			description: '挖掘家长的真实需求，而非表面需求',
			icon: '🩺',
		},
	},
	// 三诊三问 - 210帧 (7秒)
	{
		duration: 210,
		component: ContentSlide,
		props: {
			title: '三诊三问法',
			points: [
				'一诊：孩子当前英语水平如何？',
				'二诊：您期望孩子达到什么程度？',
				'三诊：您为孩子英语学习做过哪些尝试？',
				'核心：挖掘焦虑，而非推销产品',
			],
			backgroundColor:
				'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)',
		},
	},
	// 第三章标题 - 120帧 (4秒)
	{
		duration: 120,
		component: ChapterTitle,
		props: {
			chapterNumber: '第三章',
			title: '理念渗透篇',
			description: '让产品成为解决问题的最佳方案',
			icon: '💎',
		},
	},
	// FAB法则 - 180帧 (6秒)
	{
		duration: 180,
		component: FormulaCard,
		props: {
			keyword: 'FAB法则',
			meaning:
				'Feature（特征）→ Advantage（优势）→ Benefit（利益）',
			example:
				'✗ 我们是1对2教学（F）→ 能增加开口机会（A）→ 让孩子自信说英语（B）',
			icon: '🎯',
			color: '#667eea',
		},
	},
	// 三明治法则 - 180帧 (6秒)
	{
		duration: 180,
		component: FormulaCard,
		props: {
			keyword: '三明治法则',
			meaning: '认可问题 → 转换视角 → 提供方案',
			example:
				'认同价格顾虑（上层面包）+ 强调价值差异（中间肉饼）+ 呈现投资回报（下层面包）',
			icon: '🍔',
			color: '#f093fb',
		},
	},
	// 第四章标题 - 120帧 (4秒)
	{
		duration: 120,
		component: ChapterTitle,
		props: {
			chapterNumber: '第四章',
			title: '异议处理篇',
			description: '将拒绝转化为成交机会',
			icon: '🛡️',
		},
	},
	// 价格异议处理 - 210帧 (7秒)
	{
		duration: 210,
		component: DialogueSlide,
		props: {
			question: '太贵了，别家更便宜',
			answer:
				'认同您的顾虑。确实市面上有更便宜的，但教育投资要看三方面：师资、效果、孩子兴趣。我们外教全为北美认证老师，且Lily您也看到了，18个月销冠不是因为便宜，是因为有效。',
			tip: '不要反驳价格，要转换价值维度',
		},
	},
	// 等等考虑 - 210帧 (7秒)
	{
		duration: 210,
		component: DialogueSlide,
		props: {
			question: '我再考虑考虑',
			answer:
				'当然可以。想请问您，主要考虑哪方面呢？是课程安排、老师匹配，还是效果承诺？了解具体顾虑后，我能帮您更清晰评估。',
			tip: '把模糊的"考虑"转化为具体问题',
		},
	},
	// 需要问家人 - 210帧 (7秒)
	{
		duration: 210,
		component: DialogueSlide,
		props: {
			question: '我要回去问问孩子爸爸',
			answer:
				'非常好，家庭共识很重要。我发您一份课程介绍和体验课邀请，方便您和先生讨论。如果他有什么疑问，随时可以联系我。',
			tip: '成为盟友，而非对立面',
		},
	},
	// 第五章标题 - 120帧 (4秒)
	{
		duration: 120,
		component: ChapterTitle,
		props: {
			chapterNumber: '第五章',
			title: '逼单篇',
			description: '临门一脚，促成成交',
			icon: '⚽',
		},
	},
	// 逼单技巧 - 210帧 (7秒)
	{
		duration: 210,
		component: ContentSlide,
		props: {
			title: '逼单四步法',
			points: [
				'确认需求：您最看重哪方面？',
				'制造稀缺：这个时段只剩2个名额',
				'降低门槛：今天报名可赠送体验课',
				'促成决策：您看周六还是周日方便？',
			],
			backgroundColor:
				'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
		},
	},
	// 结尾 - 180帧 (6秒)
	{
		duration: 180,
		component: ContentSlide,
		props: {
			title: '销售 = 科学 + 艺术',
			points: [
				'科学：可复制的方法论和话术',
				'艺术：真诚共情和灵活应变',
				'记住：不是为了销售产品，而是帮助家长解决问题',
				'像Lily一样：准备充分，心态开放，持续学习',
			],
			backgroundColor:
				'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
		},
	},
];

export const LilySalesTraining: React.FC = () => {
	const frame = useCurrentFrame();

	// 计算总帧数
	const totalFrames = SCENES.reduce((acc, scene) => acc + scene.duration, 0);

	// 计算当前场景
	let currentFrame = 0;
	let currentSceneIndex = 0;

	for (let i = 0; i < SCENES.length; i++) {
		const sceneEnd = currentFrame + SCENES[i].duration;
		if (frame < sceneEnd) {
			currentSceneIndex = i;
			break;
		}
		currentFrame = sceneEnd;
	}

	// 场景过渡效果
	const sceneProgress =
		(frame - currentFrame + SCENES[currentSceneIndex].duration * 0.7) /
		SCENES[currentSceneIndex].duration;

	const transitionOpacity = interpolate(sceneProgress, [0, 0.3, 0.7, 1], [0, 1, 1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill>
			{SCENES.map((scene, index) => {
				const startTime = SCENES.slice(0, index).reduce(
					(acc, s) => acc + s.duration,
					0
				);
				const endTime = startTime + scene.duration;

				if (frame < startTime || frame >= endTime) {
					return null;
				}

				const SceneComponent = scene.component as React.ComponentType<any>;

				return (
					<Sequence
						key={index}
						from={startTime}
						durationInFrames={scene.duration}
					>
						<div
							style={{
								opacity: transitionOpacity,
								width: '100%',
								height: '100%',
							}}
						>
							<SceneComponent {...scene.props} />
						</div>
					</Sequence>
				);
			})}
		</AbsoluteFill>
	);
};
