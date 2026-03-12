import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {FC} from 'react';

interface DialogueSlideProps {
	question: string;
	answer: string;
	tip?: string;
	role?: string;
}

export const DialogueSlide: FC<DialogueSlideProps> = ({
	question,
	answer,
	tip,
	role = '销售顾问',
}) => {
	const frame = useCurrentFrame();

	const questionOpacity = interpolate(frame, [0, 20], [0, 1], {
		extrapolateRight: 'clamp',
	});

	const answerOpacity = interpolate(frame, [30, 50], [0, 1], {
		extrapolateRight: 'clamp',
	});

	const tipOpacity = interpolate(frame, [60, 80], [0, 1], {
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
				justifyContent: 'center',
				alignItems: 'center',
				padding: 80,
			}}
		>
			<div
				style={{
					width: '100%',
					maxWidth: 1600,
					display: 'flex',
					flexDirection: 'column',
					gap: 40,
				}}
			>
				{/* Question */}
				<div
					style={{
						background: 'white',
						padding: '40px 50px',
						borderRadius: 20,
						boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
						opacity: questionOpacity,
					}}
				>
					<div
						style={{
							fontSize: 24,
							color: '#999',
							marginBottom: 15,
							fontWeight: 'bold',
						}}
					>
						👤 家长提问
					</div>
					<div
						style={{
							fontSize: 36,
							color: '#333',
							lineHeight: 1.5,
						}}
					>
						{question}
					</div>
				</div>

				{/* Answer */}
				<div
					style={{
						background: 'white',
						padding: '40px 50px',
						borderRadius: 20,
						boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
						opacity: answerOpacity,
					}}
				>
					<div
						style={{
							fontSize: 24,
							color: '#999',
							marginBottom: 15,
							fontWeight: 'bold',
						}}
					>
						💼 {role}回应
					</div>
					<div
						style={{
							fontSize: 36,
							color: '#333',
							lineHeight: 1.5,
						}}
					>
						{answer}
					</div>
				</div>

				{/* Tip */}
				{tip && (
					<div
						style={{
							background: 'rgba(255,255,255,0.95)',
							padding: '30px 40px',
							borderRadius: 15,
							boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
							opacity: tipOpacity,
						}}
					>
						<div
							style={{
								fontSize: 28,
								color: '#e91e63',
								fontWeight: 'bold',
							}}
						>
							⭐ 技巧要点：{tip}
						</div>
					</div>
				)}
			</div>
		</AbsoluteFill>
	);
};
