const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const phaseBar = document.getElementById('phase-bar');

canvas.width = 800;
canvas.height = 600;

const TILE_SIZE = 40;
const NEON_PURPLE = "#b026ff";
const DARK_PURPLE = "#3c0a5a";
const NEON_CYAN = "#00ffff";
const YELLOW = "#ffff00";
const WALL_COLOR = "#191432";

const MAZE_DATA = [
    "11111111111111111111",
    "10000000000000000001",
    "10111011111111011101",
    "10100000011000000101",
    "10101111011011110101",
    "10001000000000010001",
    "11101011100111010111",
    "10000010000001000001",
    "10111110111101111101",
    "10000000000000000001",
    "10111011111111011101",
    "10001000011000010001",
    "11101111011011110111",
    "10000000000000000001",
    "11111111111111111111"
];

let walls = [];
let ectoplasms = [];
let GameState = "PLAYING";

const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playBeep() {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain); gain.connect(audioCtx.destination);
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
    osc.start(); osc.stop(audioCtx.currentTime + 0.1);
}

class Player {
    constructor() {
        this.reset();
    }
    reset() {
        this.x = TILE_SIZE * 1.5;
        this.y = TILE_SIZE * 1.5;
        this.radius = 14;
        this.speed = 3.0; // Slightly slower base speed because movement is automatic now
        this.vx = 0;
        this.vy = 0;
        this.phasing = false;
        this.phaseMeter = 100;
    }
    update(keys) {
        // Change direction on tap
        if (keys['w']) { this.vx = 0; this.vy = -this.speed; }
        if (keys['s']) { this.vx = 0; this.vy = this.speed; }
        if (keys['a']) { this.vx = -this.speed; this.vy = 0; }
        if (keys['d']) { this.vx = this.speed; this.vy = 0; }

        if (keys[' '] && this.phaseMeter > 0) {
            this.phasing = true;
            this.phaseMeter -= 0.6;
            phaseBar.classList.add('phasing');
        } else {
            this.phasing = false;
            if (this.phaseMeter < 100) this.phaseMeter += 0.15;
            phaseBar.classList.remove('phasing');
        }
        if (this.phaseMeter < 0) this.phaseMeter = 0;
        phaseBar.style.width = this.phaseMeter + "%";

        let nextX = this.x + this.vx;
        let nextY = this.y + this.vy;

        let collision = false;
        if (!this.phasing) {
            for (let wall of walls) {
                if (nextX + this.radius > wall.x && nextX - this.radius < wall.x + TILE_SIZE &&
                    nextY + this.radius > wall.y && nextY - this.radius < wall.y + TILE_SIZE) {
                    collision = true;
                    break;
                }
            }
        }

        if (!collision) {
            this.x = nextX;
            this.y = nextY;
        } else {
            // Stop if hit wall and NOT phasing
            this.vx = 0;
            this.vy = 0;
        }

        this.x = Math.max(this.radius, Math.min(canvas.width - this.radius, this.x));
        this.y = Math.max(this.radius, Math.min(canvas.height - this.radius, this.y));

        for (let i = ectoplasms.length - 1; i >= 0; i--) {
            let e = ectoplasms[i];
            let dist = Math.hypot(this.x - (e.x + 4), this.y - (e.y + 4));
            if (dist < this.radius + 6) {
                ectoplasms.splice(i, 1);
                playBeep();
                if (ectoplasms.length === 0) GameState = "WIN";
            }
        }
    }
    draw() {
        ctx.beginPath();ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.phasing ? DARK_PURPLE : NEON_PURPLE;
        ctx.fill();
        if (this.phasing) {
            ctx.strokeStyle = NEON_PURPLE; ctx.lineWidth = 2;
            ctx.beginPath();ctx.arc(this.x, this.y, this.radius + 4, 0, Math.PI * 2);
            ctx.stroke();
        }
    }
}

class Enemy {
    constructor(x, y, type) {
        this.x = x;
        this.y = y;
        this.type = type; // "direct", "predict", "ambush", "patrol", "random"
        this.radius = 16;
        this.speed = 1.8;
        this.vx = 0;
        this.vy = 0;
    }
    update(p) {
        let targetX = p.x;
        let targetY = p.y;

        if (this.type === "predict") {
            // Predict where player is going (target a spot 80px ahead)
            targetX = p.x + (p.vx * 25);
            targetY = p.y + (p.vy * 25);
        } else if (this.type === "ambush") {
            // Hardcode target to the center to "block" the player if they come near
            if (Math.hypot(p.x - 400, p.y - 300) > 200) {
                targetX = 400; targetY = 300;
            }
        } else if (this.type === "patrol") {
            // Circles the middle
            let time = Date.now() / 1000;
            targetX = 400 + Math.cos(time) * 200;
            targetY = 300 + Math.sin(time) * 150;
        }

        let dx = targetX - this.x;
        let dy = targetY - this.y;
        let dist = Math.hypot(dx, dy);
        
        if (dist > 5) {
            let mvx = (dx / dist) * this.speed;
            let mvy = (dy / dist) * this.speed;
            
            // Simple pathfinding: try move, if wall, slide
            if (!this.checkWall(this.x + mvx, this.y + mvy)) {
                this.x += mvx; this.y += mvy;
            } else if (!this.checkWall(this.x + mvx, this.y)) {
                this.x += mvx;
            } else if (!this.checkWall(this.x, this.y + mvy)) {
                this.y += mvy;
            }
        }

        if (Math.hypot(this.x - p.x, this.y - p.y) < this.radius + p.radius - 6) {
            GameState = "LOSS";
        }
    }
    checkWall(nx, ny) {
        for (let w of walls) {
            if (nx + this.radius > w.x && nx - this.radius < w.x + TILE_SIZE &&
                ny + this.radius > w.y && ny - this.radius < w.y + TILE_SIZE) return true;
        }
        return false;
    }
    draw() {
        ctx.fillStyle = YELLOW;
        ctx.beginPath();
        // Drawing slightly different eye colors to differentiate types
        ctx.arc(this.x, this.y, this.radius, 0.2 * Math.PI, 1.8 * Math.PI);
        ctx.lineTo(this.x, this.y);
        ctx.fill();
        ctx.fillStyle = "black";
        ctx.beginPath(); ctx.arc(this.x + 2, this.y - 6, 3, 0, Math.PI*2); ctx.fill();
    }
}

let player = new Player();
let enemies = [];
const keys = {};

function init() {
    walls = []; ectoplasms = []; enemies = []; GameState = "PLAYING";
    player.reset();
    MAZE_DATA.forEach((row, r) => {
        row.split('').forEach((char, c) => {
            let x = c * TILE_SIZE, y = r * TILE_SIZE;
            if (char === '1') walls.push({x, y});
            else if (char === '0') ectoplasms.push({x: x + 16, y: y + 16});
        });
    });
    // Add 5 Hunters with various AI behaviors
    enemies.push(new Enemy(720, 520, "direct"));  // Blinky
    enemies.push(new Enemy(720, 40, "predict"));  // Pinky
    enemies.push(new Enemy(40, 520, "patrol"));   // Inky
    enemies.push(new Enemy(400, 300, "ambush"));  // Clyde
    enemies.push(new Enemy(720, 300, "random"));  // Shadow
}

window.addEventListener('keydown', e => {
    keys[e.key.toLowerCase()] = true;
    if (e.key === 'r' && GameState !== "PLAYING") init();
    if (e.key === ' ') e.preventDefault();
});
window.addEventListener('keyup', e => keys[e.key.toLowerCase()] = false);

function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (GameState === "PLAYING") {
        player.update(keys);
        enemies.forEach(e => e.update(player));
    }
    ctx.fillStyle = WALL_COLOR; ctx.strokeStyle = NEON_PURPLE;
    walls.forEach(w => { ctx.fillRect(w.x, w.y, TILE_SIZE, TILE_SIZE); ctx.strokeRect(w.x, w.y, TILE_SIZE, TILE_SIZE); });
    ctx.fillStyle = NEON_CYAN;
    ectoplasms.forEach(e => { ctx.fillRect(e.x, e.y, 8, 8); });
    player.draw();
    enemies.forEach(e => e.draw());
    scoreElement.innerText = `Ectoplasms: ${ectoplasms.length}`;
    if (GameState !== "PLAYING") {
        ctx.fillStyle = "rgba(0,0,0,0.85)"; ctx.fillRect(0,0,canvas.width,canvas.height);
        ctx.textAlign = "center"; ctx.font = "bold 48px Arial";
        if (GameState === "WIN") { ctx.fillStyle = NEON_CYAN; ctx.fillText("YOU SURVIVED!", 400, 300); }
        else { ctx.fillStyle = NEON_PURPLE; ctx.fillText("GAME OVER!", 400, 300); }
        ctx.fillStyle = "#c8c8ff"; ctx.font = "24px Arial"; ctx.fillText("Press R to Restart", 400, 360);
    }
    requestAnimationFrame(loop);
}
init(); loop();
