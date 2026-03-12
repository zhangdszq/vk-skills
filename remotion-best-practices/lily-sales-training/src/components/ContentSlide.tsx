import {AbsoluteFill, interpolate, useCurrentFrame, spring} from 'remotion';
import {FC} from 'react';

interface ContentSlideProps {
	title: string;
	points: string[];
	highlightIndex?: number;
	backgroundColor?: string;
}

export const ContentSlide: FC<ContentSlideProps> = ({
	title,
	points,
	highlightIndex,
	backgroundColor = 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
}) => {
	const frame = useCurrentFrame();

	const titleScale = spring({
		frame,
		fps: 30,
		config: {
			damping: 100,
			stiffness: 200,
			mass: 0.5,
		},
	});

	const pointsOpacity = interpolate(frame, [20, 40], [0, 1], {
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				background: backgroundColor,
				justifyContent: 'center',
				alignItems: 'center',
				padding: 80,
			}}
		>
			<div style={{width: '100%', maxWidth: 1600, color: 'white'}}>
				<h2
					style={{
						fontSize: 56,
						fontWeight: 'bold',
						marginBottom: 60,
						textShadow: '2px 2px 4px rgba(0,0,0,0.2)',
						transform: `scale(${titleScale})`,
					}}
				>
					{title}
				</h2>
				<div style={{opacity: pointsOpacity}}>
					{points.map((point, index) => {
						const pointOpacity = interpolate(
							frame,
							[40 + index * 10, 60 + index * 10],
							[0, 1],
							{extrapolateRight: 'clamp'}
						);

						const pointTranslate = interpolate(
							frame,
							[40 + index * 10, 60 + index * 10],
							[50, 0],
							{extrapolateRight: 'clamp'}
						);

						const isHighlighted = highlightIndex === index;
						return (
							<div
								key={index}
								style={{
									fontSize: isHighlighted ? 42 : 36,
									marginBottom: 30,
									padding: isHighlighted ? '20px 30px' : '15px 20px',
									background: isHighlighted
										? 'rgba(255,255,255,0.3)'
										: 'transparent',
									borderRadius: 10,
									opacity: pointOpacity,
									transform: `translateY(${pointTranslate}px)`,
									fontWeight: isHighlighted ? 'bold' : 'normal',
								}}
							>
								<span style={{marginRight: 15}}>•</span>
								{point}
							</div>
						);
					})}
				</div>
			</div>
		</AbsoluteFill>
	);
};
