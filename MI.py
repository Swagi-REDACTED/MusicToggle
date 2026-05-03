import os
import sys
import re

# =====================================================================
# MOD FILES CONTENT
# =====================================================================

INFO_TXT = r"""{
    "Name": "Music Background Toggle",
    "ID": "bg_music_toggle",
    "Author": "Blupillcosby",
    "Description": "Toggles 'Music in background' with M (focused) or Ctrl+M (global). Fixes the game engine bug where music doesn't resume while tabbed out.",
    "ModVersion": 1.8,
    "GameVersion": 2.052,
    "Date": "03/05/2026",
    "Dependencies": [],
    "LanguagePacks": ["EN"],
    "AllowSteamAchievs": true
}"""

MAIN_JS = r"""Game.registerMod("bg_music_toggle", {
    init: function() {
        let MOD = this;
        console.log("Music Background Toggle Mod Initialized.");

        if (typeof window.api !== 'undefined') {
            window.api.send('toMain', { id: 'music_shortcut_setup' });
        }

        const performToggle = () => {
            // Toggle preference (0 is OFF, 1 is ON)
            Game.prefs.bgMusic = Game.prefs.bgMusic ? 0 : 1;
            
            // --- THE DIRECT VOLUME FIX ---
            // The game engine mutes music by setting volume to 0 on window blur.
            // We force the update by calling the native volume setter.
            if (typeof Game.setVolumeMusic === 'function') {
                if (Game.prefs.bgMusic) {
                    // Turn it ON: Restore volume immediately (Game.volumeMusic / 100)
                    Game.setVolumeMusic(Game.volumeMusic);
                } else {
                    // Turn it OFF: If window is currently blurred, we force volume to 0
                    // because the game engine only triggers the mute on the initial blur event.
                    if (!document.hasFocus() && typeof Music !== 'undefined' && Music && typeof Music.setVolume === 'function') {
                        Music.setVolume(0);
                    }
                }
            }
            
            if (typeof PlaySound === 'function') PlaySound('snd/tick.mp3');
            if (Game.onMenu === 'prefs') Game.UpdateMenu();

            Game.Notify('Music Toggle', 'Music in background: <b>' + (Game.prefs.bgMusic ? 'ON' : 'OFF') + '</b>', [1, 29], 2);
        };

        window.addEventListener('keydown', function(e) {
            const el = document.activeElement;
            const isTyping = el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);
            if (isTyping) return;
            if (e.key.toLowerCase() === 'm') performToggle();
        }, true);

        if (typeof window.api !== 'undefined') {
            window.api.receive('fromMain', (args) => {
                if (args && args.id === 'trigger_music_toggle') performToggle();
            });
        }
    }
});"""

START_JS_PATCH = r"""
			else if (req=='music_shortcut_setup')
			{
				try {
					const { globalShortcut } = require('electron');
					globalShortcut.unregister('CommandOrControl+M');
					globalShortcut.register('CommandOrControl+M', () => {
						send('trigger_music_toggle', 0, callback);
					});
				} catch(e) { console.log('Music shortcut error:', e); }
			}"""

# =====================================================================
# INSTALLER LOGIC
# =====================================================================

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def patch_start_js(filepath):
    print(f"[*] Reading target: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Aggressively remove ALL instances of the old music_shortcut_setup block
    # This prevents the "doing nothing" issue where an old block blocks the new one.
    pattern = r"else if\s*\(\s*req\s*==\s*['\"]music_shortcut_setup['\"]\s*\)"
    while True:
        match = re.search(pattern, content)
        if not match:
            break
        
        print("[*] Old music shortcut block detected. Purging...")
        start_idx = match.start()
        brace_start = content.find("{", start_idx)
        if brace_start != -1:
            brace_count = 0
            brace_end = -1
            for i in range(brace_start, len(content)):
                if content[i] == '{': brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i
                        break
            if brace_end != -1:
                content = content[:start_idx] + content[brace_end+1:]
            else:
                break
        else:
            break

    # 2. Inject fresh block after the 'save' block
    save_pattern = r"else if\s*\(\s*req\s*==\s*['\"]save['\"]\s*&&\s*args\.data\s*\)"
    save_match = re.search(save_pattern, content)
    
    if not save_match:
        print("[X] ERROR: Could not find base 'save' block in start.js!")
        return False

    brace_start = content.find("{", save_match.start())
    brace_count = 0
    brace_end = -1
    for i in range(brace_start, len(content)):
        if content[i] == '{': brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                brace_end = i
                break
    
    if brace_end == -1:
        print("[X] ERROR: Failed to parse start.js structure.")
        return False

    print("[*] Injecting global shortcut listener...")
    new_content = content[:brace_end+1] + START_JS_PATCH + content[brace_end+1:]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("[✓] Backend patch applied successfully.")
    return True

def main():
    print("==================================================")
    print("    MUSIC BACKGROUND TOGGLE MOD INSTALLER        ")
    print("==================================================")

    base_dir = get_base_dir()
    start_js_path = os.path.join(base_dir, "resources", "app", "start.js")
    mod_dir = os.path.join(base_dir, "resources", "app", "mods", "local", "MusicToggle")

    if not os.path.exists(start_js_path):
        print("[X] CRITICAL ERROR: Could not find Cookie Clicker files.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    if patch_start_js(start_js_path):
        os.makedirs(mod_dir, exist_ok=True)
        with open(os.path.join(mod_dir, "info.txt"), 'w', encoding='utf-8') as f: f.write(INFO_TXT)
        with open(os.path.join(mod_dir, "main.js"), 'w', encoding='utf-8') as f: f.write(MAIN_JS)
        print(f"[✓] Mod installed to: {mod_dir}")
        print("\n==================================================")
        print("   INSTALLATION COMPLETE! RESTART THE GAME!       ")
        print("==================================================")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()