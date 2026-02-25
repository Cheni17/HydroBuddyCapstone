"""
Sensor Log Analyzer
====================
Reads the CSV logs produced by the calibration scripts and plots them.

Usage:
    python tests/analyze_logs.py

Requires:
    pip install matplotlib pandas
"""

import sys
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
except ImportError:
    print("Install dependencies first:  pip install matplotlib pandas")
    sys.exit(1)

from config import (
    WATER_LEVEL_THRESHOLD,
    PERSON_PRESENCE_DISTANCE,
    AUDIO_THRESHOLD_DB,
    SILENCE_THRESHOLD_DB,
    MOTION_THRESHOLD,
    ERRATIC_MOTION_THRESHOLD,
)

LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')


def load_csv(name: str):
    path = os.path.join(LOGS_DIR, name)
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        return df if not df.empty else None
    except Exception as e:
        print(f"  [WARN] Could not load {name}: {e}")
        return None


def plot_distance(ax, df):
    ax.plot(df['elapsed_s'], df['distance_cm'], alpha=0.5, color='steelblue', label='Raw distance')
    ax.plot(df['elapsed_s'], df['rolling_avg_cm'], color='navy', linewidth=2, label='Rolling avg')
    ax.axhline(WATER_LEVEL_THRESHOLD,    color='red',    linestyle='--', label=f'WATER_LEVEL_THRESHOLD ({WATER_LEVEL_THRESHOLD} cm)')
    ax.axhline(PERSON_PRESENCE_DISTANCE, color='orange', linestyle='--', label=f'PERSON_PRESENCE_DISTANCE ({PERSON_PRESENCE_DISTANCE} cm)')
    ax.set_title('Distance Sensor')
    ax.set_ylabel('Distance (cm)')
    ax.set_xlabel('Time (s)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def plot_audio(ax, df):
    ax.plot(df['elapsed_s'], df['db'], alpha=0.5, color='mediumseagreen', label='Raw dB')
    ax.plot(df['elapsed_s'], df['rolling_avg_db'], color='darkgreen', linewidth=2, label='Rolling avg')
    ax.axhline(AUDIO_THRESHOLD_DB,   color='red',    linestyle='--', label=f'AUDIO_THRESHOLD_DB ({AUDIO_THRESHOLD_DB} dB)')
    ax.axhline(SILENCE_THRESHOLD_DB, color='orange', linestyle='--', label=f'SILENCE_THRESHOLD_DB ({SILENCE_THRESHOLD_DB} dB)')
    ax.set_title('Audio Sensor')
    ax.set_ylabel('Sound Level (dB)')
    ax.set_xlabel('Time (s)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def plot_motion(ax, df):
    ax.plot(df['elapsed_s'], df['net_motion_g'], alpha=0.5, color='darkorange', label='Net motion')
    ax.plot(df['elapsed_s'], df['rolling_avg_g'], color='saddlebrown', linewidth=2, label='Rolling avg')
    ax.axhline(MOTION_THRESHOLD,         color='orange', linestyle='--', label=f'MOTION_THRESHOLD ({MOTION_THRESHOLD} g)')
    ax.axhline(ERRATIC_MOTION_THRESHOLD, color='red',    linestyle='--', label=f'ERRATIC_MOTION_THRESHOLD ({ERRATIC_MOTION_THRESHOLD} g)')
    ax.set_title('Motion Sensor (MPU-6050)')
    ax.set_ylabel('Net Acceleration (g)')
    ax.set_xlabel('Time (s)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def print_summary(df, name: str, value_col: str, low_thresh: float, high_thresh: float):
    vals = df[value_col].dropna()
    print(f"\n  {name}")
    print(f"    Min:  {vals.min():.3f}   Max: {vals.max():.3f}   Avg: {vals.mean():.3f}")
    print(f"    Time below low threshold  ({low_thresh}):  {(vals < low_thresh).sum()} samples  ({100*(vals < low_thresh).mean():.1f}%)")
    print(f"    Time above high threshold ({high_thresh}): {(vals > high_thresh).sum()} samples  ({100*(vals > high_thresh).mean():.1f}%)")


def run():
    print("\n" + "=" * 60)
    print("  HydroBuddy — Sensor Log Analyzer")
    print("=" * 60)

    dist_df   = load_csv('distance_log.csv')
    audio_df  = load_csv('audio_log.csv')
    motion_df = load_csv('motion_log.csv')

    available = [df for df in [dist_df, audio_df, motion_df] if df is not None]
    if not available:
        print("\n  No log files found. Run the calibration scripts first:\n")
        print("    python tests/calibrate_distance.py")
        print("    python tests/calibrate_audio.py")
        print("    python tests/calibrate_motion.py\n")
        return

    # Print text summaries
    print("\n  Threshold Analysis:")
    if dist_df is not None:
        print_summary(dist_df,   "Distance",  'distance_cm',  WATER_LEVEL_THRESHOLD, PERSON_PRESENCE_DISTANCE)
    if audio_df is not None:
        print_summary(audio_df,  "Audio",     'db',           SILENCE_THRESHOLD_DB,  AUDIO_THRESHOLD_DB)
    if motion_df is not None:
        print_summary(motion_df, "Motion",    'net_motion_g', MOTION_THRESHOLD,      ERRATIC_MOTION_THRESHOLD)

    # Plot
    num_plots = len(available)
    fig = plt.figure(figsize=(14, 4 * num_plots))
    fig.suptitle('HydroBuddy — Sensor Calibration Logs', fontsize=14, fontweight='bold')
    gs  = gridspec.GridSpec(num_plots, 1, hspace=0.45)

    plot_idx = 0
    if dist_df is not None:
        plot_distance(fig.add_subplot(gs[plot_idx]), dist_df)
        plot_idx += 1
    if audio_df is not None:
        plot_audio(fig.add_subplot(gs[plot_idx]), audio_df)
        plot_idx += 1
    if motion_df is not None:
        plot_motion(fig.add_subplot(gs[plot_idx]), motion_df)

    output_path = os.path.join(LOGS_DIR, 'calibration_report.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n  Chart saved to: {output_path}")
    print("=" * 60 + "\n")
    plt.show()


if __name__ == "__main__":
    run()
