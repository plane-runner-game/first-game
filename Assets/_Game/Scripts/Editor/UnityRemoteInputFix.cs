// UnityRemoteInputFix.cs (Editor only)
// Makes touches from the Unity Remote 5 app reach the Input System in this editor version.
// The Input System package (1.20) hooks Unity Remote through UnityEditor.Remote.GenericRemote and
// looks for that class in UnityEditor.CoreModule. In Unity 6000.6 the class lives in
// UnityEditor.GenericRemoteModule, so the package never registers its message handler: the
// picture streams to the phone, the Hello message never arrives, no Touchscreen device is created
// and every tap is dropped (found 2026-09-17: "it works but I can't play"). This registers the
// package's own handler with the right module after every domain reload.
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.InputSystem;

namespace SkySquad.EditorTools
{
    public static class UnityRemoteInputFix
    {
        [InitializeOnLoadMethod]
        static void Register()
        {
            try
            {
                const BindingFlags any = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static;
                var core = typeof(EditorApplication).Assembly;
                if (core.GetType("UnityEditor.Remote.GenericRemote") != null) return;   // the package finds it itself: nothing to fix

                Type genericRemote = null;
                foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                {
                    if (asm.GetName().Name != "UnityEditor.GenericRemoteModule") continue;
                    genericRemote = asm.GetType("UnityEditor.Remote.GenericRemote");
                    break;
                }
                if (genericRemote == null) return;

                var support = typeof(InputSystem).Assembly.GetType("UnityEngine.InputSystem.UnityRemoteSupport");
                var getHandler = support?.GetMethod("GetMessageHandlerForTesting", any);
                var handler = getHandler?.Invoke(null, null) as Func<IntPtr, bool>;
                if (handler == null) return;

                genericRemote.GetMethod("AddMessageHandler", any)?.Invoke(null, new object[] { handler });
                Debug.Log("[UnityRemoteInputFix] Input System handler registered with UnityEditor.GenericRemoteModule");
            }
            catch (Exception e)
            {
                Debug.LogWarning("[UnityRemoteInputFix] could not register: " + e.Message);
            }
        }
    }
}
