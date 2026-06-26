import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

const CONNECTIONS = [
  [0,1],[1,2],[2,3],[3,4],
  [0,5],[5,6],[6,7],[7,8],
  [0,9],[9,10],[10,11],[11,12],
  [0,13],[13,14],[14,15],[15,16],
  [0,17],[17,18],[18,19],[19,20],
  [5,9],[9,13],[13,17],
];

function HandSkeleton({ landmarks, color }) {
  const points = useMemo(() => {
    if (!landmarks || landmarks.length < 21) return null;
    return landmarks.map((lm) => [lm.x * 2 - 1, -(lm.y * 2 - 1), lm.z]);
  }, [landmarks]);

  if (!points) return null;

  const jointSize = Math.max(0.015, 0.04 - Math.abs(points[0]?.[2] || 0) * 0.02);

  return (
    <group>
      {CONNECTIONS.map(([i, j], idx) => (
        <line key={`b-${idx}`}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([
                points[i][0], points[i][1], points[i][2],
                points[j][0], points[j][1], points[j][2],
              ])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color={color} transparent opacity={0.6} linewidth={1} />
        </line>
      ))}
      {points.map((p, i) => (
        <mesh key={`j-${i}`} position={p}>
          <sphereGeometry args={[jointSize, 8, 8]} />
          <meshBasicMaterial color={color} transparent opacity={0.9} />
        </mesh>
      ))}
    </group>
  );
}

export default function HandView({ hands }) {
  if (!hands || hands.length === 0) return null;

  return (
    <Canvas
      camera={{ position: [0, 0, 2.2], fov: 40 }}
      style={{ background: 'transparent' }}
      gl={{ alpha: true }}
    >
      <ambientLight intensity={1} />
      {hands.map((hand, i) => (
        <HandSkeleton
          key={i}
          landmarks={hand.landmarks}
          color={hand.handedness === 'Left' ? '#60a5fa' : '#f472b6'}
        />
      ))}
    </Canvas>
  );
}
