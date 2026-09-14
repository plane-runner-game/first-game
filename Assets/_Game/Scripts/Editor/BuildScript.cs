// BuildScript.cs (Editor only)
// Command-line builds:
//   Unity.exe -batchmode -projectPath <proj> -executeMethod SkySquad.EditorTools.BuildScript.BuildWindows -quit
//   Unity.exe -batchmode -projectPath <proj> -executeMethod SkySquad.EditorTools.BuildScript.BuildAndroid -quit
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static class BuildScript
    {
        static string[] Scenes => new[] { "Assets/_Game/Scenes/Main.unity" };

        [MenuItem("Sky Squad/Build Windows (test player)")]
        public static void BuildWindows()
        {
            Directory.CreateDirectory("Builds/Windows");
            var opts = new BuildPlayerOptions
            {
                scenes = Scenes,
                locationPathName = "Builds/Windows/SkySquad.exe",
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None
            };
            var report = BuildPipeline.BuildPlayer(opts);
            Report(report);
        }

        [MenuItem("Sky Squad/Build Android (APK)")]
        public static void BuildAndroid()
        {
            Directory.CreateDirectory("Builds/Android");
            EditorUserBuildSettings.buildAppBundle = false;
            var opts = new BuildPlayerOptions
            {
                scenes = Scenes,
                locationPathName = "Builds/Android/SkySquad.apk",
                target = BuildTarget.Android,
                options = BuildOptions.None
            };
            var report = BuildPipeline.BuildPlayer(opts);
            Report(report);
        }

        static void Report(BuildReport report)
        {
            var s = report.summary;
            Debug.Log("[SkySquad] Build " + s.result + " -> " + s.outputPath + " (" + (s.totalSize / (1024 * 1024)) + " MB, " + s.totalTime.TotalSeconds.ToString("0") + " s, errors " + s.totalErrors + ")");
            if (s.result != BuildResult.Succeeded) EditorApplication.Exit(1);
        }
    }
}
