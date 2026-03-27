import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

export class VRMLoader {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.renderer = null;
        this.scene = null;
        this.camera = null;
        this.vrm = null;
        this.mixer = null;
        this.clock = new THREE.Clock();

        // Lip-sync & Procedural Anim states
        this.blinkTimer = 0;
        this.blinkInterval = 3 + Math.random() * 2; // Random blink interval
        this.isSpeaking = false;

        this.init();
    }

    init() {
        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            alpha: true,
            antialias: true
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.outputEncoding = THREE.sRGBEncoding;

        // Scene
        this.scene = new THREE.Scene();

        // Camera
        this.camera = new THREE.PerspectiveCamera(30, window.innerWidth / window.innerHeight, 0.1, 100);
        // Position camera to focus on VRM (a bit to the left of center as per spec)
        this.camera.position.set(-0.3, 1.4, 3.5);

        // Light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
        directionalLight.position.set(1, 1, 1);
        this.scene.add(directionalLight);

        // Window resize
        window.addEventListener('resize', () => {
            this.renderer.setSize(window.innerWidth, window.innerHeight);
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
        });

        this.animate();
    }

    async loadVRM(url) {
        const loader = new GLTFLoader();
        loader.register((parser) => new VRMLoaderPlugin(parser));

        return new Promise((resolve, reject) => {
            loader.load(
                url,
                (gltf) => {
                    const vrm = gltf.userData.vrm;
                    VRMUtils.removeUnnecessaryJoints(gltf.scene);

                    // Rotate for better view if needed
                    // vrm.scene.rotation.y = Math.PI;

                    this.scene.add(vrm.scene);
                    this.vrm = vrm;
                    console.log("VRM loaded successfully");
                    resolve(vrm);
                },
                (progress) => {
                    console.log('Loading VRM...', (progress.loaded / progress.total * 100), '%');
                },
                (error) => {
                    console.error('Error loading VRM:', error);
                    reject(error);
                }
            );
        });
    }

    animate() {
        requestAnimationFrame(this.animate.bind(this));

        const delta = this.clock.getDelta();
        if (this.vrm) {
            this.vrm.update(delta);
            this.updateProceduralAnimations(delta);
        }

        this.renderer.render(this.scene, this.camera);
    }

    updateProceduralAnimations(delta) {
        if (!this.vrm) return;

        // Breathing
        const breathAmount = 0.05 * Math.sin(this.clock.elapsedTime * 1.5);
        this.vrm.humanoid.getNormalizedBoneNode('chest').rotation.x = breathAmount * 0.2;

        // Blinking
        this.blinkTimer += delta;
        if (this.blinkTimer > this.blinkInterval) {
            const blinkValue = Math.max(0, 1 - Math.abs(Math.sin((this.blinkTimer - this.blinkInterval) * 10)));
            this.vrm.expressionManager.setValue('blink', blinkValue);

            if (this.blinkTimer > this.blinkInterval + 0.3) {
                this.vrm.expressionManager.setValue('blink', 0);
                this.blinkTimer = 0;
                this.blinkInterval = 2 + Math.random() * 4;
            }
        }

        // Lip-sync (A-I-U-E-O)
        if (this.isSpeaking) {
            const mouthOpen = Math.abs(Math.sin(this.clock.elapsedTime * 15)) * 0.7;
            this.vrm.expressionManager.setValue('aa', mouthOpen);
            this.vrm.expressionManager.setValue('ih', mouthOpen * 0.2);
            this.vrm.expressionManager.setValue('ou', mouthOpen * 0.1);
        } else {
            this.vrm.expressionManager.setValue('aa', 0);
            this.vrm.expressionManager.setValue('ih', 0);
            this.vrm.expressionManager.setValue('ou', 0);
        }
    }

    setSpeaking(speaking) {
        this.isSpeaking = speaking;
    }
}
