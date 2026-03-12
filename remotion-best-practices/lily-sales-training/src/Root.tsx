import {Composition} from 'remotion';
import {LilySalesTraining} from './compositions/LilySalesTraining';

export const RemotionRoot: React.FC = () => {
	return (
		<>
			<Composition
				id="LilySalesTraining"
				component={LilySalesTraining}
				durationInFrames={900} // 30秒 @ 30fps
				fps={30}
				width={1920}
				height={1080}
				defaultProps={{
					theme: 'light',
				}}
			/>
		</>
	);
};
