import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const CargoVisualization = ({ items }) => {
  const mountRef = useRef(null);

  useEffect(() => {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf9fafb);

    const camera = new THREE.PerspectiveCamera(
      75,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(10, 6, 10);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mountRef.current.appendChild(renderer.domElement);

    // Enhanced lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 15, 10);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);

    // Create detailed truck
    const createDetailedTruck = () => {
      const truck = new THREE.Group();

      // Trailer (cargo space)
      const trailerGroup = new THREE.Group();
      
      // Main trailer body
      const trailerGeometry = new THREE.BoxGeometry(7.2, 2.8, 2.5);
      const trailerMaterial = new THREE.MeshPhongMaterial({
        color: 0x666666,
        transparent: true,
        opacity: 0.3,
      });
      const trailer = new THREE.Mesh(trailerGeometry, trailerMaterial);
      trailer.position.y = 1.4;
      trailer.receiveShadow = true;
      trailerGroup.add(trailer);

      // Trailer frame
      const frameGeometry = new THREE.BoxGeometry(7.4, 0.2, 2.6);
      const frameMaterial = new THREE.MeshPhongMaterial({ color: 0x333333 });
      const frame = new THREE.Mesh(frameGeometry, frameMaterial);
      frame.position.y = 0.1;
      frame.castShadow = true;
      trailerGroup.add(frame);

      // Trailer supports
      const supportGeometry = new THREE.BoxGeometry(0.1, 1, 2.6);
      const supportMaterial = new THREE.MeshPhongMaterial({ color: 0x444444 });
      
      // Add supports at regular intervals
      for (let x = -3.6; x <= 3.6; x += 1.2) {
        const support = new THREE.Mesh(supportGeometry, supportMaterial);
        support.position.set(x, 1.4, 0);
        support.castShadow = true;
        trailerGroup.add(support);
      }

      truck.add(trailerGroup);

      // Detailed cab
      const cabGroup = new THREE.Group();

      // Main cab body
      const cabBodyGeometry = new THREE.BoxGeometry(2.2, 2.2, 2.3);
      const cabMaterial = new THREE.MeshPhongMaterial({ 
        color: 0x2563eb,
        metalness: 0.6,
        roughness: 0.4
      });
      const cabBody = new THREE.Mesh(cabBodyGeometry, cabMaterial);
      cabBody.position.set(-4.5, 1.1, 0);
      cabBody.castShadow = true;
      cabGroup.add(cabBody);

      // Windshield
      const windshieldGeometry = new THREE.PlaneGeometry(1.5, 1);
      const windshieldMaterial = new THREE.MeshPhongMaterial({ 
        color: 0x88ccff,
        transparent: true,
        opacity: 0.6
      });
      const windshield = new THREE.Mesh(windshieldGeometry, windshieldMaterial);
      windshield.position.set(-3.6, 1.6, 0);
      windshield.rotation.set(0, Math.PI / 2, 0);
      cabGroup.add(windshield);

      truck.add(cabGroup);

      // Enhanced wheels
      const createWheel = () => {
        const wheelGroup = new THREE.Group();

        // Tire
        const tireGeometry = new THREE.CylinderGeometry(0.4, 0.4, 0.35, 32);
        const tireMaterial = new THREE.MeshPhongMaterial({ 
          color: 0x1a1a1a,
          roughness: 0.7 
        });
        const tire = new THREE.Mesh(tireGeometry, tireMaterial);
        tire.rotation.z = Math.PI / 2;
        tire.castShadow = true;
        wheelGroup.add(tire);

        // Hub cap
        const hubGeometry = new THREE.CylinderGeometry(0.2, 0.2, 0.36, 16);
        const hubMaterial = new THREE.MeshPhongMaterial({ 
          color: 0xcccccc,
          metalness: 0.8 
        });
        const hub = new THREE.Mesh(hubGeometry, hubMaterial);
        hub.rotation.z = Math.PI / 2;
        wheelGroup.add(hub);

        return wheelGroup;
      };

      // Add wheels with proper positioning
      const wheelPositions = [
        [-4.5, -1.2], // Front left
        [-4.5, 1.2],  // Front right
        [-1, -1.2],   // Back left 1
        [-1, 1.2],    // Back right 1
        [1, -1.2],    // Back left 2
        [1, 1.2],     // Back right 2
      ];

      wheelPositions.forEach(([x, z]) => {
        const wheel = createWheel();
        wheel.position.set(x, 0.4, z);
        truck.add(wheel);
      });

      return truck;
    };

    const truck = createDetailedTruck();
    scene.add(truck);

    // Ground plane
    const groundGeometry = new THREE.PlaneGeometry(30, 30);
    const groundMaterial = new THREE.MeshPhongMaterial({ 
      color: 0xe5e7eb,
      side: THREE.DoubleSide 
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // Optimized packing algorithm
    const packItems = (items) => {
      // Sort items by volume in descending order
      const sortedItems = [...items].sort((a, b) => {
        const getVolume = (item) => {
          const [l, w, h] = item.dimensions
            .split('x')
            .map(dim => parseFloat(dim.trim()) / 100);
          return l * w * h;
        };
        return getVolume(b) - getVolume(a);
      });

      const spaces = [{
        x: -2.8,
        y: 0.1,
        z: -1,
        width: 5.6,
        height: 2.6,
        depth: 2
      }];

      sortedItems.forEach(item => {
        const [length, width, height] = item.dimensions
          .split('x')
          .map(dim => parseFloat(dim.trim()) / 100);

        // Try different orientations
        const orientations = [
          [length, width, height],
          [length, height, width],
          [width, length, height],
          [width, height, length],
          [height, length, width],
          [height, width, length]
        ];

        let bestFit = null;
        let bestSpace = null;
        let bestOrientation = null;

        orientations.forEach(([l, w, h]) => {
          spaces.forEach(space => {
            if (l <= space.width && h <= space.height && w <= space.depth) {
              if (!bestFit || space.y < bestSpace.y || 
                 (space.y === bestSpace.y && space.x < bestSpace.x)) {
                bestFit = { x: space.x, y: space.y, z: space.z };
                bestSpace = space;
                bestOrientation = [l, w, h];
              }
            }
          });
        });

        if (bestFit && bestOrientation) {
          const [l, w, h] = bestOrientation;
          
          // Create and position the box
          const geometry = new THREE.BoxGeometry(l, h, w);
          const material = new THREE.MeshPhongMaterial({
            color: item.status === 'ready' ? 0x4ade80 : 0xfbbf24,
            transparent: true,
            opacity: 0.8,
          });
          
          const box = new THREE.Mesh(geometry, material);
          box.castShadow = true;
          box.position.set(
            bestFit.x + l/2,
            bestFit.y + h/2,
            bestFit.z + w/2
          );
          
          scene.add(box);

          // Split remaining space
          const newSpaces = [];
          
          // Split vertically
          if (h < bestSpace.height) {
            newSpaces.push({
              x: bestSpace.x,
              y: bestFit.y + h,
              z: bestSpace.z,
              width: bestSpace.width,
              height: bestSpace.height - h,
              depth: bestSpace.depth
            });
          }

          // Split horizontally
          if (l < bestSpace.width) {
            newSpaces.push({
              x: bestFit.x + l,
              y: bestSpace.y,
              z: bestSpace.z,
              width: bestSpace.width - l,
              height: h,
              depth: bestSpace.depth
            });
          }

          // Split depth-wise
          if (w < bestSpace.depth) {
            newSpaces.push({
              x: bestSpace.x,
              y: bestSpace.y,
              z: bestFit.z + w,
              width: l,
              height: h,
              depth: bestSpace.depth - w
            });
          }

          // Remove used space and add new spaces
          spaces.splice(spaces.indexOf(bestSpace), 1, ...newSpaces);
        }
      });
    };

    packItems(items);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 5;
    controls.maxDistance = 20;
    controls.target.set(0, 1, 0);

    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      camera.aspect = mountRef.current.clientWidth / mountRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      mountRef.current?.removeChild(renderer.domElement);
      scene.clear();
    };
  }, [items]);

  return <div ref={mountRef} className="w-full h-full" />;
};

export default CargoVisualization;