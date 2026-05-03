Game.registerMod("bg_music_toggle", {
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
});