# 🎸 MusicManiac: 3D Arena Shooter


## 📋 Overview
**MusicManiac** is a 3D arena shooter developed for the Computer Graphics course at the **University of Algarve** (2024/2025). The project focuses on low-level 3D rendering using **Python and OpenGL**, giving full control over the rendering pipeline, shaders, and matrix transformations.

In this world, music is your only weapon. Players fight enemies using various musical instruments, each featuring unique combat behaviors inspired by classic shooter mechanics.

---

## 🚀 Technical Highlights
This project demonstrates core competencies in:
* **Graphics Pipeline:** Implementation of real-time lighting (Ambient, Directional, and Point Lights) using the **Phong Reflection Model**.
* **3D Math:** Manipulation of transformation matrices for camera movement (FPS Rig), object rotation, and projection systems.
* **Collision Systems:** Custom AABB (Axis-Aligned Bounding Box) logic and 3D proximity detection for gameplay mechanics.
* **Asset Management:** Loading and rendering complex .obj models and managing textures using PyOpenGL and custom readers.
* **State Management:** A robust game state system allowing transitions between menus, "Musical Attack" mode, and "Music Defense" mode.

---

## 🎮 Game Modes

| Mode | Description |
| :--- | :--- |
| **Musical Attack** | Survival mode against continuous waves of enemies with increasing difficulty. |
| **Music Defense** | Strategic mode where players must protect a central instrument pile from being destroyed. |

### 🛠️ Musical Arsenal
* **Guitar:** Long-range precision weapon firing fast musical notes.
* **Sax Tuba:** Explosive projectile weapon that releases sub-notes upon impact (shrapnel effect).
* **French Horn:** Short-range spread weapon firing multiple notes in a cone.
* **Ocarina:** Tactical throwable grenade dealing area-of-effect (AoE) damage.

---

## 🛠️ Technologies
* **Language:** Python 3
* **Graphics:** PyOpenGL (OpenGL 3.3+)
* **Framework:** Pygame (Input, Event Handling, and Audio)
* **Modeling:** Blender (Custom 3D Assets)
* **Audio:** FL Studio (Original Soundtrack and SFX)

---

## 💻 How to Run
1. Ensure you have Python installed.
2. Install the required dependencies:
   pip install -r requirements.txt
3. Run the game via the main menu:
   python main_menu.py

---

## 👥 Development Team
* André Guerreiro
* Rui Saraiva
* Sérgio Boico
* Vasco Evaristo

---
*Academic project developed for the Computer Graphics course.*
