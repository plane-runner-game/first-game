// UnityRemoteInputShim.cs
// Makes Unity Remote touch input reach the Input System in Unity 6.6.
//
// The Input System package (1.20) hooks Unity Remote by looking up UnityEditor.Remote.GenericRemote inside
// the assembly that holds EditorApplication. In Unity 6.6 that class moved to UnityEditor.GenericRemoteModule,
// so the lookup returns null, the package never installs its message handler, and the remote Touchscreen
// device is never created: the phone shows the stream but its touches go nowhere ("I can just watch").
// This editor-only shim finds GenericRemote wherever it lives, takes the package's own handler through the
// internal accessor it exposes for its tests, and registers it - after that the package does the rest
// (the console logs "Unity Remote connected to input!" when the phone connects in Play mode).
using System;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;

namespace SkySquad.EditorTools
{
    [InitializeOnLoad]
    public static class UnityRemoteInputShim
    {
        const string QualityKey = "SkySquad.UnityRemoteQualityApplied.v2";

        /// <summary>Full Game-view resolution instead of the default downsized stream ("the resolution on my phone is so bad"), but JPEG
        /// frames: PNG at full size ran at ~4 fps with a long delay. Applied once automatically; the menu item re-applies it.
        /// The Game view size is the other half: keep it around 720 x 1560 (portrait) - the stream is the Game view, pixel for pixel.</summary>
        [MenuItem("Sky Squad/Unity Remote: sharp stream")]
        public static void SharpStream()
        {
            EditorSettings.unityRemoteResolution = "Normal";
            EditorSettings.unityRemoteCompression = "JPEG";
            EditorPrefs.SetBool(QualityKey, true);
            Debug.Log("[SkySquad] Unity Remote stream set to Normal resolution + JPEG. Keep the Game view portrait and modest (about 720x1560): bigger views mean lower frame rate on the phone.");
        }

        static UnityRemoteInputShim()
        {
            if (!EditorPrefs.GetBool(QualityKey, false)) SharpStream();
            try
            {
                var support = AppDomain.CurrentDomain.GetAssemblies()
                    .Select(a => a.GetType("UnityEngine.InputSystem.UnityRemoteSupport"))
                    .FirstOrDefault(t => t != null);
                if (support == null) return;
                var getHandler = support.GetMethod("GetMessageHandlerForTesting", BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public);
                if (getHandler == null) return;
                var handler = getHandler.Invoke(null, null);
                if (handler == null) return;

                var remote = AppDomain.CurrentDomain.GetAssemblies()
                    .Select(a => a.GetType("UnityEditor.Remote.GenericRemote"))
                    .FirstOrDefault(t => t != null);
                if (remote == null) return;
                var remove = remote.GetMethod("RemoveMessageHandler");
                var add = remote.GetMethod("AddMessageHandler");
                if (add == null) return;
                remove?.Invoke(null, new[] { handler });   // never twice
                add.Invoke(null, new[] { handler });
            }
            catch (Exception e)
            {
                Debug.LogWarning("[SkySquad] Unity Remote input shim could not install: " + e.Message);
            }
        }
    }
}
