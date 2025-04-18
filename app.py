from flask import Flask, render_template_string

app = Flask(__name__)


@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Particle Flower Garden</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                overflow: hidden;
                background-color: #283618;
                font-family: Arial, sans-serif;
                color: #fefae0;
            }

            #garden-container {
                position: relative;
                width: 100vw;
                height: 100vh;
            }

            #garden-canvas {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                cursor: pointer;
            }

            .title-overlay {
                position: absolute;
                top: 20px;
                left: 20px;
                z-index: 10;
                padding: 10px 15px;
                background-color: rgba(60, 60, 50, 0.7);
                border-radius: 8px;
                pointer-events: none;
            }

            .controls-overlay {
                position: absolute;
                bottom: 20px;
                right: 20px;
                z-index: 10;
                display: flex;
                gap: 10px;
            }

            button {
                background-color: #606c38;
                color: #fefae0;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.3s;
            }

            button:hover {
                background-color: #dda15e;
            }

            .color-picker {
                display: flex;
                gap: 8px;
                margin-bottom: 10px;
            }

            .color-option {
                width: 25px;
                height: 25px;
                border-radius: 50%;
                cursor: pointer;
                border: 2px solid transparent;
                transition: transform 0.2s;
            }

            .color-option:hover {
                transform: scale(1.2);
            }

            .color-option.selected {
                border-color: #fff;
            }

            @keyframes sway {
                0% {
                    transform: rotate(0deg);
                }
                25% {
                    transform: rotate(3deg);
                }
                50% {
                    transform: rotate(0deg);
                }
                75% {
                    transform: rotate(-3deg);
                }
                100% {
                    transform: rotate(0deg);
                }
            }

            .flower-container {
                position: absolute;
                transform-origin: bottom center;
                animation: sway 4s ease-in-out infinite;
            }

            /* Different sway timings for visual variety */
            .flower-container:nth-child(2n) {
                animation-duration: 5s;
            }

            .flower-container:nth-child(3n) {
                animation-duration: 6s;
            }

            .flower-container:nth-child(4n) {
                animation-delay: 1s;
            }
        </style>
    </head>
    <body>
        <div id="garden-container">
            <canvas id="garden-canvas"></canvas>

            <div class="title-overlay">
                <h1>Particle Flower Garden</h1>
                <p>Click and drag to create flowers</p>
            </div>

            <div class="controls-overlay">
                <div>
                    <div class="color-picker">
                        <!-- Default colors -->
                        <div class="color-option selected" style="background-color: #ff7eb9;" data-color="#ff7eb9"></div>
                        <div class="color-option" style="background-color: #7afcff;" data-color="#7afcff"></div>
                        <div class="color-option" style="background-color: #feff9c;" data-color="#feff9c"></div>
                        <div class="color-option" style="background-color: #fff740;" data-color="#fff740"></div>
                        <div class="color-option" style="background-color: #ff65a3;" data-color="#ff65a3"></div>
                    </div>
                    <button id="clear-btn">Clear Garden</button>
                </div>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', () => {
                // Canvas setup
                const canvas = document.getElementById('garden-canvas');
                const ctx = canvas.getContext('2d');
                const gardenContainer = document.getElementById('garden-container');

                // Set canvas dimensions
                function resizeCanvas() {
                    canvas.width = window.innerWidth;
                    canvas.height = window.innerHeight;
                }

                resizeCanvas();
                window.addEventListener('resize', resizeCanvas);

                // Particle and Flower classes/state
                let isDrawing = false;
                let currentPath = [];
                let flowers = [];
                let currentColor = '#ff7eb9'; // Default color

                // Color selection handling
                const colorOptions = document.querySelectorAll('.color-option');
                colorOptions.forEach(option => {
                    option.addEventListener('click', () => {
                        // Remove selected class from all options
                        colorOptions.forEach(o => o.classList.remove('selected'));
                        // Add selected class to clicked option
                        option.classList.add('selected');
                        // Update current color
                        currentColor = option.getAttribute('data-color');
                    });
                });

                // Clear button
                const clearBtn = document.getElementById('clear-btn');
                clearBtn.addEventListener('click', () => {
                    flowers = [];
                    // Clear the canvas
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    // Remove all flower DOM elements
                    document.querySelectorAll('.flower-container').forEach(el => el.remove());
                });

                // Classes for our flower system
                class Vector2 {
                    constructor(x, y) {
                        this.x = x;
                        this.y = y;
                    }

                    add(v) {
                        return new Vector2(this.x + v.x, this.y + v.y);
                    }

                    subtract(v) {
                        return new Vector2(this.x - v.x, this.y - v.y);
                    }

                    multiply(scalar) {
                        return new Vector2(this.x * scalar, this.y * scalar);
                    }

                    length() {
                        return Math.sqrt(this.x * this.x + this.y * this.y);
                    }

                    normalize() {
                        const len = this.length();
                        if (len === 0) return new Vector2(0, 0);
                        return new Vector2(this.x / len, this.y / len);
                    }

                    rotate(angle) {
                        const cos = Math.cos(angle);
                        const sin = Math.sin(angle);
                        return new Vector2(
                            this.x * cos - this.y * sin,
                            this.x * sin + this.y * cos
                        );
                    }
                }

                class Particle {
                    constructor(position, velocity, color, size, life = 1.0) {
                        this.position = position;
                        this.velocity = velocity;
                        this.color = color;
                        this.baseSize = size;
                        this.size = 0; // Start small and grow
                        this.life = life;
                        this.decay = 0.01; // How fast life decreases
                        this.growing = true;
                        this.growSpeed = 0.1;
                    }

                    update() {
                        // Update position based on velocity
                        this.position = this.position.add(this.velocity);

                        // Handle growth animation
                        if (this.growing) {
                            this.size += this.growSpeed;
                            if (this.size >= this.baseSize) {
                                this.size = this.baseSize;
                                this.growing = false;
                            }
                        }

                        // Decrease life
                        this.life -= this.decay;

                        return this.life > 0;
                    }

                    draw(ctx) {
                        // Set opacity based on life
                        const alpha = this.life > 0.8 ? 1.0 : this.life + 0.2;

                        // Extract RGB from hex color
                        const r = parseInt(this.color.slice(1, 3), 16);
                        const g = parseInt(this.color.slice(3, 5), 16);
                        const b = parseInt(this.color.slice(5, 7), 16);

                        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;

                        // Draw petal shape using bezier curves
                        ctx.beginPath();
                        ctx.moveTo(this.position.x, this.position.y);

                        // Control points for bezier curve to create petal shape
                        const angle = Math.atan2(this.velocity.y, this.velocity.x);
                        const length = this.size;

                        // Endpoint of the petal
                        const end = new Vector2(
                            this.position.x + length * Math.cos(angle),
                            this.position.y + length * Math.sin(angle)
                        );

                        // Control points perpendicular to the direction
                        const perpAngle = angle + Math.PI / 2;
                        const controlDist = length * 0.5;

                        const ctrl1 = new Vector2(
                            this.position.x + controlDist * Math.cos(perpAngle),
                            this.position.y + controlDist * Math.sin(perpAngle)
                        );

                        const ctrl2 = new Vector2(
                            end.x + controlDist * Math.cos(perpAngle),
                            end.y + controlDist * Math.sin(perpAngle)
                        );

                        // Draw the curve
                        ctx.bezierCurveTo(ctrl1.x, ctrl1.y, ctrl2.x, ctrl2.y, end.x, end.y);

                        // Draw the other side of the petal
                        const ctrl3 = new Vector2(
                            end.x - controlDist * Math.cos(perpAngle),
                            end.y - controlDist * Math.sin(perpAngle)
                        );

                        const ctrl4 = new Vector2(
                            this.position.x - controlDist * Math.cos(perpAngle),
                            this.position.y - controlDist * Math.sin(perpAngle)
                        );

                        ctx.bezierCurveTo(ctrl3.x, ctrl3.y, ctrl4.x, ctrl4.y, this.position.x, this.position.y);

                        ctx.closePath();
                        ctx.fill();
                    }
                }

                class Flower {
                    constructor(position, color) {
                        this.position = position;
                        this.color = color;
                        this.particles = [];
                        this.bloomState = 0;
                        this.bloomSpeed = 0.02;
                        this.maxPetals = Math.floor(Math.random() * 5) + 8; // 8-12 petals
                        this.size = Math.random() * 15 + 20; // Random size between 20-35
                        this.createFlower();
                    }

                    createFlower() {
                        // Create center of the flower
                        const centerColor = this.lightenColor(this.color, 50);

                        // Create petals around the center
                        for (let i = 0; i < this.maxPetals; i++) {
                            const angle = (i / this.maxPetals) * Math.PI * 2;
                            const petalPosition = new Vector2(
                                this.position.x + Math.cos(angle) * (this.size * 0.2),
                                this.position.y + Math.sin(angle) * (this.size * 0.2)
                            );

                            const petalVelocity = new Vector2(
                                Math.cos(angle) * 0.2,
                                Math.sin(angle) * 0.2
                            );

                            // Small variance in petal colors
                            const variance = Math.floor(Math.random() * 30) - 15;
                            const petalColor = this.lightenColor(this.color, variance);

                            this.particles.push(new Particle(
                                petalPosition,
                                petalVelocity,
                                petalColor,
                                this.size * (0.8 + Math.random() * 0.4), // Vary petal sizes
                                1.0
                            ));
                        }

                        // Add center particles
                        for (let i = 0; i < 6; i++) {
                            const angle = (i / 6) * Math.PI * 2;
                            const centerPosition = new Vector2(
                                this.position.x + Math.cos(angle) * (this.size * 0.1),
                                this.position.y + Math.sin(angle) * (this.size * 0.1)
                            );

                            this.particles.push(new Particle(
                                centerPosition,
                                new Vector2(0, 0),
                                centerColor,
                                this.size * 0.5,
                                1.0
                            ));
                        }

                        // Create the stem using DOM elements for CSS animation
                        this.createDOMElements();
                    }

                    createDOMElements() {
                        // Create a container for the flower stem that will animate
                        const flowerContainer = document.createElement('div');
                        flowerContainer.className = 'flower-container';
                        flowerContainer.style.left = `${this.position.x}px`;
                        flowerContainer.style.top = `${this.position.y}px`;

                        // Add random animation delay for varied movement
                        flowerContainer.style.animationDelay = `${Math.random() * 2}s`;

                        gardenContainer.appendChild(flowerContainer);
                    }

                    update() {
                        // Update bloom state
                        this.bloomState = Math.min(1.0, this.bloomState + this.bloomSpeed);

                        // Update all particles
                        this.particles.forEach(particle => {
                            particle.update();
                        });

                        return true; // Flowers don't die in this garden
                    }

                    draw(ctx) {
                        // Draw all particles
                        this.particles.forEach(particle => {
                            particle.draw(ctx);
                        });
                    }

                    // Helper to lighten or darken colors
                    lightenColor(color, amount) {
                        // Convert hex to RGB
                        let r = parseInt(color.slice(1, 3), 16);
                        let g = parseInt(color.slice(3, 5), 16);
                        let b = parseInt(color.slice(5, 7), 16);

                        // Adjust RGB values
                        r = Math.min(255, Math.max(0, r + amount));
                        g = Math.min(255, Math.max(0, g + amount));
                        b = Math.min(255, Math.max(0, b + amount));

                        // Convert back to hex
                        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
                    }
                }

                // Path drawing and particle generation
                function generatePathParticles(start, end) {
                    const direction = end.subtract(start);
                    const distance = direction.length();

                    if (distance < 5) return; // Skip if points are too close

                    // Normalize direction and create particles along path
                    const normalizedDir = direction.normalize();
                    const particleCount = Math.ceil(distance / 10); // One particle every 10px

                    for (let i = 0; i < particleCount; i++) {
                        const t = i / particleCount;
                        const pos = start.add(direction.multiply(t));

                        // Add some randomness to position
                        const randOffset = new Vector2(
                            (Math.random() - 0.5) * 10,
                            (Math.random() - 0.5) * 10
                        );

                        const particlePos = pos.add(randOffset);

                        // Create trail particle with velocity perpendicular to direction
                        const perpAngle = Math.atan2(normalizedDir.y, normalizedDir.x) + (Math.PI / 2);
                        const perpVector = new Vector2(
                            Math.cos(perpAngle),
                            Math.sin(perpAngle)
                        ).multiply(Math.random() * 2 - 1); // Random direction

                        currentPath.push({
                            position: particlePos,
                            velocity: perpVector,
                        });
                    }
                }

                // Mouse event handlers
                canvas.addEventListener('mousedown', (e) => {
                    isDrawing = true;
                    currentPath = [];

                    const mousePos = new Vector2(e.clientX, e.clientY);
                    currentPath.push({
                        position: mousePos,
                        velocity: new Vector2(0, 0)
                    });
                });

                canvas.addEventListener('mousemove', (e) => {
                    if (!isDrawing) return;

                    const mousePos = new Vector2(e.clientX, e.clientY);
                    const lastPos = currentPath.length > 0 
                        ? currentPath[currentPath.length - 1].position 
                        : mousePos;

                    generatePathParticles(lastPos, mousePos);
                });

                function endDrawing(e) {
                    if (!isDrawing) return;
                    isDrawing = false;

                    if (currentPath.length > 0) {
                        // Create a flower at the end of the path
                        const lastPos = currentPath[currentPath.length - 1].position;
                        flowers.push(new Flower(lastPos, currentColor));
                    }
                }

                canvas.addEventListener('mouseup', endDrawing);
                canvas.addEventListener('mouseleave', endDrawing);

                // Touch event handlers for mobile support
                canvas.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    const touch = e.touches[0];
                    isDrawing = true;
                    currentPath = [];

                    const touchPos = new Vector2(touch.clientX, touch.clientY);
                    currentPath.push({
                        position: touchPos,
                        velocity: new Vector2(0, 0)
                    });
                });

                canvas.addEventListener('touchmove', (e) => {
                    e.preventDefault();
                    if (!isDrawing) return;

                    const touch = e.touches[0];
                    const touchPos = new Vector2(touch.clientX, touch.clientY);
                    const lastPos = currentPath.length > 0 
                        ? currentPath[currentPath.length - 1].position 
                        : touchPos;

                    generatePathParticles(lastPos, touchPos);
                });

                function endTouchDrawing(e) {
                    e.preventDefault();
                    if (!isDrawing) return;
                    isDrawing = false;

                    if (currentPath.length > 0) {
                        // Create a flower at the end of the path
                        const lastPos = currentPath[currentPath.length - 1].position;
                        flowers.push(new Flower(lastPos, currentColor));
                    }
                }

                canvas.addEventListener('touchend', endTouchDrawing);
                canvas.addEventListener('touchcancel', endTouchDrawing);

                // Animation loop
                function animate() {
                    // Clear the canvas
                    ctx.clearRect(0, 0, canvas.width, canvas.height);

                    // Draw path particles
                    if (isDrawing && currentPath.length > 0) {
                        for (const point of currentPath) {
                            const particle = new Particle(
                                point.position,
                                point.velocity,
                                currentColor,
                                8 + Math.random() * 4,
                                0.8
                            );
                            particle.size = particle.baseSize; // Show full size immediately
                            particle.draw(ctx);
                        }
                    }

                    // Update and draw flowers
                    flowers.forEach(flower => {
                        flower.update();
                        flower.draw(ctx);
                    });

                    requestAnimationFrame(animate);
                }

                // Start animation
                animate();

                // Optional: Add background elements
                function drawBackground() {
                    // Add subtle grass texture at the bottom
                    const grassHeight = canvas.height * 0.1;
                    const grassGradient = ctx.createLinearGradient(0, canvas.height - grassHeight, 0, canvas.height);
                    grassGradient.addColorStop(0, 'rgba(76, 154, 42, 0.2)');
                    grassGradient.addColorStop(1, 'rgba(82, 121, 65, 0.4)');

                    ctx.fillStyle = grassGradient;
                    ctx.fillRect(0, canvas.height - grassHeight, canvas.width, grassHeight);
                }
            });
        </script>
    </body>
    </html>
    ''')


if __name__ == '__main__':
    app.run(debug=True, port=5000)