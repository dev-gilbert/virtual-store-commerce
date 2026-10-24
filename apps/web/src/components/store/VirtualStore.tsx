"use client";

import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

type Vec3 = [number, number, number];

function Shelf({ position }: { position: Vec3 }) {
  return (
    <group position={position}>
      {[-0.9, 0.9].map((x) => (
        <mesh key={x} position={[x, 0.9, 0]}>
          <boxGeometry args={[0.08, 1.8, 0.72]} />
          <meshStandardMaterial color="#777b7c" metalness={0.25} roughness={0.55} />
        </mesh>
      ))}
      {[0.35, 0.8, 1.25, 1.7].map((y) => (
        <mesh key={y} position={[0, y, 0]}>
          <boxGeometry args={[1.9, 0.07, 0.82]} />
          <meshStandardMaterial color="#d8d5ce" roughness={0.65} />
        </mesh>
      ))}
      {Array.from({ length: 18 }, (_, index) => {
        const column = index % 9;
        const row = Math.floor(index / 9);
        const colors = ["#c78d4b", "#799d79", "#bd6c60", "#d8c16a", "#7c91b2"];
        return (
          <mesh
            key={index}
            position={[-0.78 + column * 0.195, 0.53 + row * 0.45, 0.08]}
            castShadow
          >
            <boxGeometry args={[0.14, 0.27, 0.25]} />
            <meshStandardMaterial color={colors[index % colors.length]} roughness={0.48} />
          </mesh>
        );
      })}
    </group>
  );
}

function InteractiveDrawer() {
  const [open, setOpen] = useState(false);

  return (
    <group position={[3.1, 0, 0.6]}>
      <mesh position={[0, 0.72, 0]} castShadow>
        <boxGeometry args={[1.5, 1.44, 0.95]} />
        <meshStandardMaterial color="#82796e" roughness={0.72} />
      </mesh>
      <group
        position={[0, 0.86, open ? 0.85 : 0.42]}
        onClick={(event) => {
          event.stopPropagation();
          setOpen((value) => !value);
        }}
      >
        <mesh castShadow>
          <boxGeometry args={[1.22, 0.3, 0.7]} />
          <meshStandardMaterial color={open ? "#d9c5a7" : "#b3a087"} />
        </mesh>
        {open &&
          Array.from({ length: 4 }, (_, index) => (
            <mesh key={index} position={[-0.42 + index * 0.28, 0.19, 0]}>
              <cylinderGeometry args={[0.07, 0.07, 0.22, 16]} />
              <meshStandardMaterial color={["#d4a14e", "#799b7a"][index % 2]} />
            </mesh>
          ))}
      </group>
    </group>
  );
}

function StoreScene() {
  return (
    <>
      <color attach="background" args={["#e9e7e1"]} />
      <ambientLight intensity={1.15} />
      <hemisphereLight args={["#ffffff", "#b9b3a8", 1.2]} />
      <directionalLight
        position={[6, 10, 5]}
        intensity={2.1}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.06, 0]} receiveShadow>
        <planeGeometry args={[32, 32]} />
        <meshStandardMaterial color="#c9c7c0" roughness={0.9} />
      </mesh>

      <mesh position={[0, 2.5, -5]} receiveShadow>
        <boxGeometry args={[14, 5, 0.18]} />
        <meshStandardMaterial color="#f4f1ea" />
      </mesh>

      <Shelf position={[-3.1, 0, -2.1]} />
      <Shelf position={[-3.1, 0, 1.5]} />
      <Shelf position={[0, 0, -2.1]} />
      <Shelf position={[0, 0, 1.5]} />
      <InteractiveDrawer />

      <OrbitControls
        makeDefault
        target={[0, 1, 0]}
        minDistance={3}
        maxDistance={17}
        maxPolarAngle={Math.PI / 2 - 0.04}
        enableDamping
        dampingFactor={0.08}
      />
    </>
  );
}

export default function VirtualStore() {
  return (
    <div className="virtual-store-canvas" aria-label="Interactive 3D supermarket prototype">
      <Canvas
        shadows
        dpr={[1, 1.5]}
        camera={{ position: [8, 6, 10], fov: 42, near: 0.1, far: 100 }}
        gl={{ antialias: true, powerPreference: "high-performance" }}
      >
        <StoreScene />
      </Canvas>
      <div className="scene-hint">
        Drag to look around · Scroll to zoom · Click the cabinet drawer
      </div>
    </div>
  );
}
