import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';

function Ring({ active }) {
  const ref = useRef();
  const hueRef = useRef(0.55);

  useFrame((_, delta) => {
    if (!ref.current) return;
    hueRef.current += delta * 0.04;
    const pulse = active
      ? 0.15 + Math.sin(hueRef.current * 6) * 0.06
      : 0.08 + Math.sin(hueRef.current * 1.5) * 0.03;
    ref.current.scale.setScalar(1 + pulse);
    ref.current.material.opacity = 0.15 + pulse * 0.5;
    ref.current.rotation.z += delta * (active ? 0.3 : 0.1);
  });

  return (
    <mesh ref={ref} rotation={[-Math.PI / 3, 0, 0]}>
      <torusGeometry args={[1.2, 0.008, 16, 100]} />
      <meshBasicMaterial color="#60a5fa" transparent opacity={0.12} />
    </mesh>
  );
}

export default function AmbientRing({ active }) {
  return (
    <Canvas
      camera={{ position: [0, 0, 3], fov: 50 }}
      style={{ background: 'transparent', pointerEvents: 'none' }}
      gl={{ alpha: true }}
    >
      <Ring active={active} />
    </Canvas>
  );
}
