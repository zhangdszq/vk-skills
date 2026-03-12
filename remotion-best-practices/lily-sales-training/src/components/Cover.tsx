import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {FC} from 'react';

interface CoverProps {
	title: string;
	subtitle: string;
}

export const Cover: FC<CoverProps> = ({title, subtitle}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	const opacity = interpolate(frame, [0, 30], [0, 1], {
		extrapolateRight: 'clamp',
	});

	const scale = interpolate(frame, [0, 30], [0.8, 1], {
		extrapolateRight: 'clamp',
	});

	const subtitleOpacity = interpolate(frame, [30, 60], [0, 1], {
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill
			style={{
				background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
				justifyContent: 'center',
				alignItems: 'center',
			}}
		>
			<div
				style={{
					textAlign: 'center',
					color: 'white',
					transform: `scale(${scale})`,
					opacity,
				}}
			>
				<h1
					style={{
						fontSize: 120,
						fontWeight: 'bold',
						margin: 0,
						textShadow: '4px 4px 8px rgba(0,0,0,0.3)',
						lineHeight: 1.2,
					}}
				>
					{title}
				</h1>
				<p
					style={{
						fontSize: 48,
						marginTop: 40,
						opacity: subtitleOpacity,
						fontWeight: 300,
					}}
				>
					{subtitle}
				</p>
			</div>
		</AbsoluteFill>
	);
};
