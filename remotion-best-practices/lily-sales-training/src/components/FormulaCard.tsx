import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {FC} from 'react';

interface FormulaCardProps {
	keyword: string;
	meaning: string;
	example?: string;
	icon?: string;
	color?: string;
}

export const FormulaCard: FC<FormulaCardProps> = ({
	keyword,
	meaning,
	example,
	icon = '💡',
	color = '#4facfe',
}) => {
	const frame = useCurrentFrame();

	const scale = interpolate(frame, [0, 20], [0.5, 1], {
		extrapolateRight: 'clamp',
	});

	const opacity = interpolate(frame, [0, 20], [0, 1], {
		extrapolateRight: 'clamp',
	});

	const contentOpacity = interpolate(frame, [20, 40], [0, 1], {
		extrapolateRight: 'clamp',
	});

	const exampleOpacity = interpolate(frame, [40, 60], [0, 1], {
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
				justifyContent: 'center',
				alignItems: 'center',
				padding: 100,
			}}
		>
			<div
				style={{
					background: 'white',
					borderRadius: 30,
					padding: 80,
					width: '100%',
					maxWidth: 1500,
					boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
					transform: `scale(${scale})`,
					opacity,
				}}
			>
				<div style={{textAlign: 'center'}}>
					<div
						style={{
							fontSize: 80,
							marginBottom: 20,
						}}
					>
						{icon}
					</div>
					<h1
						style={{
							fontSize: 72,
							fontWeight: 'bold',
							margin: 0,
							color: '#333',
							marginBottom: 40,
						}}
					>
						{keyword}
					</h1>
					<div style={{opacity: contentOpacity}}>
						<div
							style={{
								fontSize: 36,
								color: '#666',
								lineHeight: 1.6,
								marginBottom: 40,
							}}
						>
							{meaning}
						</div>
						{example && (
							<div style={{opacity: exampleOpacity}}>
								<div
									style={{
										background: '#f0f0f0',
										padding: '30px 40px',
										borderRadius: 15,
										fontSize: 28,
										color: '#444',
									}}
								>
									<strong>💬 示例：</strong> {example}
								</div>
							</div>
						)}
					</div>
				</div>
			</div>
		</AbsoluteFill>
	);
};
