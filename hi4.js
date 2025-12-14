import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Droplet, Flame, Zap, Mountain, Trees, Users, Skull, Sun, Home, Sprout } from 'lucide-react';

const WorldBoxGame = () => {
  const canvasRef = useRef(null);
  const [selectedTool, setSelectedTool] = useState('grass');
  const [isPaused, setIsPaused] = useState(false);
  const [brushSize, setBrushSize] = useState(1);
  const [stats, setStats] = useState({ 
    humans: 0, 
    animals: 0, 
    trees: 0,
    buildings: 0,
    generation: 0 
  });
  const gameStateRef = useRef(null);
  const statsHistoryRef = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const gridSize = 4;
    const cols = Math.floor(canvas.width / gridSize);
    const rows = Math.floor(canvas.height / gridSize);

    // Terrain types
    const TERRAIN = {
      WATER: 0,
      SAND: 1,
      GRASS: 2,
      DIRT: 3,
      STONE: 4,
      SNOW: 5
    };

    // Entity class with improved AI
    class Entity {
      constructor(x, y, type) {
        this.x = x;
        this.y = y;
        this.type = type;
        this.vx = (Math.random() - 0.5) * 1.5;
        this.vy = (Math.random() - 0.5) * 1.5;
        this.health = 100;
        this.age = 0;
        this.food = 100;
        this.speed = type === 'animal' ? 2 : 1;
        this.reproductionCooldown = 0;
        this.targetX = null;
        this.targetY = null;
        this.fleeX = null;
        this.fleeY = null;
      }

      findNearestFood(world, trees) {
        let nearest = null;
        let minDist = Infinity;
        
        for (let y = Math.max(0, Math.floor(this.y) - 10); y < Math.min(rows, Math.floor(this.y) + 10); y++) {
          for (let x = Math.max(0, Math.floor(this.x) - 10); x < Math.min(cols, Math.floor(this.x) + 10); x++) {
            if (world[y][x] === TERRAIN.GRASS) {
              const dist = Math.hypot(x - this.x, y - this.y);
              if (dist < minDist) {
                minDist = dist;
                nearest = { x, y };
              }
            }
          }
        }
        return nearest;
      }

      findNearestThreat(fires) {
        let nearest = null;
        let minDist = Infinity;
        
        fires.forEach(fire => {
          const dist = Math.hypot(fire.x - this.x, fire.y - this.y);
          if (dist < 15 && dist < minDist) {
            minDist = dist;
            nearest = { x: fire.x, y: fire.y };
          }
        });
        
        return nearest;
      }

      update(world, entities, trees, fires, buildings) {
        this.age++;
        this.food -= 0.08;
        this.reproductionCooldown = Math.max(0, this.reproductionCooldown - 1);

        if (this.food <= 0 || this.age > 6000 || this.health <= 0) {
          return false; // Die
        }

        // Check for fire damage
        const onFire = fires.find(f => Math.floor(f.x) === Math.floor(this.x) && Math.floor(f.y) === Math.floor(this.y));
        if (onFire) {
          this.health -= 10;
          return this.health > 0;
        }

        // AI: Flee from fire
        const threat = this.findNearestThreat(fires);
        if (threat) {
          this.fleeX = threat.x;
          this.fleeY = threat.y;
        } else {
          this.fleeX = null;
          this.fleeY = null;
        }

        // AI: Seek food when hungry
        if (this.food < 50 && !this.fleeX) {
          const food = this.findNearestFood(world, trees);
          if (food) {
            this.targetX = food.x;
            this.targetY = food.y;
          }
        } else if (this.food > 80) {
          this.targetX = null;
          this.targetY = null;
        }

        // Movement logic
        if (this.fleeX !== null) {
          // Flee from threat
          const dx = this.x - this.fleeX;
          const dy = this.y - this.fleeY;
          const dist = Math.hypot(dx, dy);
          if (dist > 0) {
            this.vx = (dx / dist) * this.speed * 1.5;
            this.vy = (dy / dist) * this.speed * 1.5;
          }
        } else if (this.targetX !== null) {
          // Move towards target
          const dx = this.targetX - this.x;
          const dy = this.targetY - this.y;
          const dist = Math.hypot(dx, dy);
          if (dist < 1) {
            this.targetX = null;
            this.targetY = null;
          } else {
            this.vx = (dx / dist) * this.speed;
            this.vy = (dy / dist) * this.speed;
          }
        } else {
          // Random wandering
          if (Math.random() < 0.03) {
            this.vx = (Math.random() - 0.5) * this.speed;
            this.vy = (Math.random() - 0.5) * this.speed;
          }
        }

        let newX = this.x + this.vx;
        let newY = this.y + this.vy;

        // Boundary check
        if (newX < 0 || newX >= cols || newY < 0 || newY >= rows) {
          this.vx *= -1;
          this.vy *= -1;
          return true;
        }

        // Terrain check
        const terrain = world[Math.floor(newY)][Math.floor(newX)];
        if (terrain !== TERRAIN.WATER) {
          this.x = newX;
          this.y = newY;
          
          // Eat grass
          if (terrain === TERRAIN.GRASS && this.food < 100) {
            this.food = Math.min(100, this.food + 15);
          }

          // Reproduction
          if (this.type === 'human' && this.food > 70 && this.age > 200 && this.reproductionCooldown === 0) {
            const nearby = entities.filter(e => 
              e.type === 'human' && 
              e !== this && 
              Math.hypot(e.x - this.x, e.y - this.y) < 3
            );
            if (nearby.length > 0 && Math.random() < 0.01) {
              this.reproductionCooldown = 500;
              return 'reproduce';
            }
          }

          // Animals reproduce too
          if (this.type === 'animal' && this.food > 70 && this.age > 150 && this.reproductionCooldown === 0) {
            const nearby = entities.filter(e => 
              e.type === 'animal' && 
              e !== this && 
              Math.hypot(e.x - this.x, e.y - this.y) < 3
            );
            if (nearby.length > 0 && Math.random() < 0.02) {
              this.reproductionCooldown = 400;
              return 'reproduce';
            }
          }
        } else {
          this.vx *= -1;
          this.vy *= -1;
        }

        return true;
      }
    }

    // Initialize world
    const world = Array(rows).fill(null).map(() => Array(cols).fill(TERRAIN.GRASS));
    const entities = [];
    const trees = [];
    const fires = [];
    const buildings = [];

    // Generate initial terrain with better algorithm
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const noise = Math.random();
        const nearWater = Math.random() < 0.08;
        
        if (nearWater) {
          world[y][x] = TERRAIN.WATER;
        } else if (noise < 0.05) {
          world[y][x] = TERRAIN.SAND;
        } else if (noise < 0.85) {
          world[y][x] = TERRAIN.GRASS;
        } else if (noise < 0.95) {
          world[y][x] = TERRAIN.STONE;
        }
      }
    }

    // Add initial trees with density check
    for (let i = 0; i < 80; i++) {
      const x = Math.floor(Math.random() * cols);
      const y = Math.floor(Math.random() * rows);
      if (world[y][x] === TERRAIN.GRASS && !trees.find(t => t.x === x && t.y === y)) {
        trees.push({ x, y, age: 0, health: 100 });
      }
    }

    gameStateRef.current = { world, entities, trees, fires, buildings };

    // Color mapping with better colors
    const colors = {
      [TERRAIN.WATER]: '#2196f3',
      [TERRAIN.SAND]: '#ffd54f',
      [TERRAIN.GRASS]: '#66bb6a',
      [TERRAIN.DIRT]: '#795548',
      [TERRAIN.STONE]: '#757575',
      [TERRAIN.SNOW]: '#eceff1'
    };

    let animationId;
    let lastUpdate = Date.now();
    let generation = 0;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw terrain
      for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
          ctx.fillStyle = colors[world[y][x]];
          ctx.fillRect(x * gridSize, y * gridSize, gridSize, gridSize);
        }
      }

      // Draw buildings
      buildings.forEach(building => {
        ctx.fillStyle = '#8d6e63';
        ctx.fillRect(building.x * gridSize, building.y * gridSize, gridSize * 2, gridSize * 2);
        ctx.fillStyle = '#5d4037';
        ctx.fillRect(building.x * gridSize, building.y * gridSize, gridSize * 2, gridSize);
      });

      // Draw trees
      trees.forEach(tree => {
        if (tree.health > 0) {
          ctx.fillStyle = '#388e3c';
          ctx.beginPath();
          ctx.arc(tree.x * gridSize + gridSize/2, tree.y * gridSize + gridSize/2, gridSize/1.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = '#2e7d32';
          ctx.fillRect(tree.x * gridSize + 1, tree.y * gridSize + 2, 2, gridSize - 2);
        }
      });

      // Draw fires with flicker
      fires.forEach(fire => {
        const flicker = Math.random() * 0.4 + 0.6;
        const time = Date.now() / 100;
        const offset = Math.sin(time + fire.x + fire.y) * 0.5;
        ctx.fillStyle = `rgba(255, ${Math.floor(140 * flicker)}, 0, ${flicker})`;
        ctx.fillRect(fire.x * gridSize, fire.y * gridSize - offset, gridSize, gridSize + offset);
      });

      // Draw entities with better visuals
      entities.forEach(entity => {
        if (entity.type === 'human') {
          // Body
          ctx.fillStyle = '#ffc107';
          ctx.fillRect(entity.x * gridSize - 1, entity.y * gridSize - 1, gridSize + 2, gridSize + 2);
          // Head
          ctx.fillStyle = '#ffb300';
          ctx.fillRect(entity.x * gridSize, entity.y * gridSize, gridSize, 2);
        } else if (entity.type === 'animal') {
          ctx.fillStyle = '#8d6e63';
          ctx.beginPath();
          ctx.arc(entity.x * gridSize + gridSize/2, entity.y * gridSize + gridSize/2, gridSize/1.5, 0, Math.PI * 2);
          ctx.fill();
        }
      });

      animationId = requestAnimationFrame(draw);
    };

    const update = () => {
      generation++;
      
      // Update entities with proper removal
      const newEntities = [];
      const entitiesToAdd = [];
      
      entities.forEach(entity => {
        const result = entity.update(world, entities, trees, fires, buildings);
        if (result === 'reproduce') {
          newEntities.push(entity);
          entitiesToAdd.push(new Entity(
            entity.x + (Math.random() - 0.5) * 2,
            entity.y + (Math.random() - 0.5) * 2,
            entity.type
          ));
        } else if (result) {
          newEntities.push(entity);
        }
      });
      
      entities.length = 0;
      entities.push(...newEntities, ...entitiesToAdd);

      // Update fires with spread limit
      const firesToRemove = [];
      const firesToAdd = [];
      
      fires.forEach((fire, idx) => {
        fire.life--;
        
        // Spread fire with cooldown
        if (Math.random() < 0.05 && fires.length < 100) {
          const dirs = [[0,1], [1,0], [0,-1], [-1,0], [1,1], [-1,-1], [1,-1], [-1,1]];
          const dir = dirs[Math.floor(Math.random() * dirs.length)];
          const nx = fire.x + dir[0];
          const ny = fire.y + dir[1];
          
          if (nx >= 0 && nx < cols && ny >= 0 && ny < rows) {
            const tree = trees.find(t => t.x === nx && t.y === ny && t.health > 0);
            if (tree && !fires.find(f => f.x === nx && f.y === ny)) {
              firesToAdd.push({ x: nx, y: ny, life: 60 });
              tree.health = 0;
            }
          }
        }

        if (fire.life <= 0) {
          firesToRemove.push(idx);
          if (fire.y < rows && fire.x < cols) {
            world[fire.y][fire.x] = TERRAIN.DIRT;
          }
        }
      });

      // Remove fires properly
      firesToRemove.reverse().forEach(idx => fires.splice(idx, 1));
      fires.push(...firesToAdd);

      // Grow trees with density check
      if (Math.random() < 0.008 && trees.filter(t => t.health > 0).length < 300) {
        const x = Math.floor(Math.random() * cols);
        const y = Math.floor(Math.random() * rows);
        const nearby = trees.filter(t => Math.hypot(t.x - x, t.y - y) < 5).length;
        if (world[y][x] === TERRAIN.GRASS && !trees.find(t => t.x === x && t.y === y) && nearby < 8) {
          trees.push({ x, y, age: 0, health: 100 });
        }
      }

      // Update stats
      const currentStats = {
        humans: entities.filter(e => e.type === 'human').length,
        animals: entities.filter(e => e.type === 'animal').length,
        trees: trees.filter(t => t.health > 0).length,
        buildings: buildings.length,
        generation: Math.floor(generation / 20)
      };
      
      setStats(currentStats);
      
      // Track history
      if (generation % 20 === 0) {
        statsHistoryRef.current.push({...currentStats, tick: generation});
        if (statsHistoryRef.current.length > 100) {
          statsHistoryRef.current.shift();
        }
      }
    };

    let updateInterval = setInterval(() => {
      if (!isPaused) {
        update();
      }
    }, 50);

    draw();

    const handleClick = useCallback((e) => {
      const rect = canvas.getBoundingClientRect();
      const centerX = Math.floor((e.clientX - rect.left) / gridSize);
      const centerY = Math.floor((e.clientY - rect.top) / gridSize);

      // Apply brush size
      for (let dy = -brushSize + 1; dy < brushSize; dy++) {
        for (let dx = -brushSize + 1; dx < brushSize; dx++) {
          const x = centerX + dx;
          const y = centerY + dy;
          
          if (x < 0 || x >= cols || y < 0 || y >= rows) continue;
          if (brushSize > 1 && Math.hypot(dx, dy) >= brushSize) continue;

          switch (selectedTool) {
            case 'water':
              world[y][x] = TERRAIN.WATER;
              break;
            case 'sand':
              world[y][x] = TERRAIN.SAND;
              break;
            case 'grass':
              world[y][x] = TERRAIN.GRASS;
              break;
            case 'stone':
              world[y][x] = TERRAIN.STONE;
              break;
            case 'tree':
              if (world[y][x] === TERRAIN.GRASS && !trees.find(t => t.x === x && t.y === y)) {
                trees.push({ x, y, age: 0, health: 100 });
              }
              break;
            case 'human':
              if (entities.filter(e => e.type === 'human').length < 200) {
                entities.push(new Entity(x + 0.5, y + 0.5, 'human'));
              }
              break;
            case 'animal':
              if (entities.filter(e => e.type === 'animal').length < 200) {
                entities.push(new Entity(x + 0.5, y + 0.5, 'animal'));
              }
              break;
            case 'building':
              if (world[y][x] === TERRAIN.GRASS && !buildings.find(b => b.x === x && b.y === y)) {
                buildings.push({ x, y });
              }
              break;
            case 'fire':
              if (!fires.find(f => f.x === x && f.y === y)) {
                fires.push({ x, y, life: 100 });
                const tree = trees.find(t => t.x === x && t.y === y);
                if (tree) tree.health = 0;
              }
              break;
            case 'lightning':
              for (let ly = -3; ly <= 3; ly++) {
                for (let lx = -3; lx <= 3; lx++) {
                  const nx = x + lx;
                  const ny = y + ly;
                  if (nx >= 0 && nx < cols && ny >= 0 && ny < rows && Math.hypot(lx, ly) < 4) {
                    if (Math.random() < 0.6) {
                      const tree = trees.find(t => t.x === nx && t.y === ny);
                      if (tree) tree.health = 0;
                      
                      // Remove entities properly
                      for (let i = entities.length - 1; i >= 0; i--) {
                        if (Math.floor(entities[i].x) === nx && Math.floor(entities[i].y) === ny) {
                          entities.splice(i, 1);
                        }
                      }
                      
                      if (!fires.find(f => f.x === nx && f.y === ny) && Math.random() < 0.4) {
                        fires.push({ x: nx, y: ny, life: 80 });
                      }
                    }
                  }
                }
              }
              break;
            case 'delete':
              world[y][x] = TERRAIN.GRASS;
              const treeIdx = trees.findIndex(t => t.x === x && t.y === y);
              if (treeIdx !== -1) trees.splice(treeIdx, 1);
              const fireIdx = fires.findIndex(f => f.x === x && f.y === y);
              if (fireIdx !== -1) fires.splice(fireIdx, 1);
              const buildingIdx = buildings.findIndex(b => b.x === x && b.y === y);
              if (buildingIdx !== -1) buildings.splice(buildingIdx, 1);
              for (let i = entities.length - 1; i >= 0; i--) {
                if (Math.floor(entities[i].x) === x && Math.floor(entities[i].y) === y) {
                  entities.splice(i, 1);
                }
              }
              break;
          }
        }
      }
    }, [selectedTool, brushSize]);

    canvas.addEventListener('click', handleClick);

    return () => {
      cancelAnimationFrame(animationId);
      clearInterval(updateInterval);
      canvas.removeEventListener('click', handleClick);
    };
  }, [selectedTool, isPaused, brushSize]);

  const tools = [
    { id: 'grass', icon: Sun, label: 'Grass', color: 'bg-green-500' },
    { id: 'water', icon: Droplet, label: 'Water', color: 'bg-blue-500' },
    { id: 'sand', icon: Mountain, label: 'Sand', color: 'bg-yellow-600' },
    { id: 'stone', icon: Mountain, label: 'Stone', color: 'bg-gray-500' },
    { id: 'tree', icon: Trees, label: 'Tree', color: 'bg-green-700' },
    { id: 'human', icon: Users, label: 'Human', color: 'bg-yellow-400' },
    { id: 'animal', icon: Users, label: 'Animal', color: 'bg-amber-700' },
    { id: 'building', icon: Home, label: 'Building', color: 'bg-orange-700' },
    { id: 'fire', icon: Flame, label: 'Fire', color: 'bg-red-500' },
    { id: 'lightning', icon: Zap, label: 'Lightning', color: 'bg-yellow-300' },
    { id: 'delete', icon: Skull, label: 'Delete', color: 'bg-red-700' }
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 p-4">
      <div className="bg-gray-800 rounded-lg shadow-2xl p-6 max-w-4xl w-full">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-white">God Simulator</h1>
          <div className="flex gap-2">
            <select 
              value={brushSize}
              onChange={(e) => setBrushSize(Number(e.target.value))}
              className="px-3 py-2 rounded bg-gray-700 text-white"
            >
              <option value={1}>Brush: Small</option>
              <option value={2}>Brush: Medium</option>
              <option value={3}>Brush: Large</option>
            </select>
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`px-4 py-2 rounded ${isPaused ? 'bg-green-600' : 'bg-yellow-600'} text-white font-semibold`}
            >
              {isPaused ? '▶ Resume' : '⏸ Pause'}
            </button>
          </div>
        </div>

        <div className="bg-gray-700 p-3 rounded mb-4">
          <div className="grid grid-cols-5 gap-4 text-white text-sm">
            <div className="flex items-center gap-1">
              <span className="text-yellow-400">👤</span> Humans: <strong>{stats.humans}</strong>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-amber-600">🦌</span> Animals: <strong>{stats.animals}</strong>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-green-400">🌲</span> Trees: <strong>{stats.trees}</strong>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-orange-400">🏠</span> Buildings: <strong>{stats.buildings}</strong>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-purple-400">⏱</span> Gen: <strong>{stats.generation}</strong>
            </div>
          </div>
        </div>

        <canvas
          ref={canvasRef}
          width={600}
          height={400}
          className="border-4 border-gray-600 rounded mb-4 cursor-crosshair bg-gray-900"
        />

        <div className="grid grid-cols-6 gap-2 mb-4">
          {tools.map(tool => {
            const Icon = tool.icon;
            return (
              <button
                key={tool.id}
                onClick={() => setSelectedTool(tool.id)}
                title={tool.label}
                className={`flex flex-col items-center justify-center p-3 rounded transition-all ${
                  selectedTool === tool.id
                    ? `${tool.color} scale-105 shadow-lg ring-2 ring-white`
                    : 'bg-gray-700 hover:bg-gray-600'
                } text-white`}
              >
                <Icon size={20} />
                <span className="text-xs mt-1">{tool.label}</span>
              </button>
            );
          })}
        </div>

        <div className="bg-gray-700 p-3 rounded text-gray-300 text-sm">
          <p className="font-semibold mb-2">🎮 Features:</p>
          <ul className="space-y-1 text-xs">
            <li>• <strong>Smart AI:</strong> Creatures seek food, flee from fire, and reproduce</li>
            <li>• <strong>Reproduction:</strong> Entities mate when well-fed and near each other</li>
            <li>• <strong>Fire Physics:</strong> Spreads naturally with population limits</li>
            <li>• <strong>Brush Size:</strong> Use dropdown to paint larger areas</li>
            <li>• <strong>Buildings:</strong> Decorative structures for your civilization</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default WorldBoxGame;