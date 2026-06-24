"""
train.py — Fine-tune or continue training the YourDiary base LSTM model.

Usage:
  python3 train.py --data your_text.txt
  python3 train.py --data corpus.txt --epochs 20 --lr 0.003 --seq 30
  python3 train.py --data diary_samples.txt --epochs 5 --lr 0.001  # light fine-tune
  python3 train.py --data corpus.txt --from-scratch               # fresh weights

This script:
  1. Loads current base_model.npz weights (fine-tune) OR starts fresh (--from-scratch)
  2. Trains on the provided text file for N epochs
  3. Saves updated weights back to base_model.npz
  4. Shows loss curve and improvement over time

Fine-tuning tips:
  - Use a lower learning rate (0.001–0.003) when fine-tuning existing weights
  - Use a higher learning rate (0.005–0.01) when training from scratch
  - More epochs = better fit, but watch for overfitting on small datasets
  - Use diary-style text to bias the model toward personal writing suggestions
"""

import numpy as np
import argparse
import os
import time
from models.lstm_model import LSTM, voc


# ─── Args ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Fine-tune the YourDiary base LSTM model")
    p.add_argument("--data",         type=str,   required=True,  help="Path to training text file (.txt)")
    p.add_argument("--epochs",       type=int,   default=10,     help="Number of training epochs (default: 10)")
    p.add_argument("--lr",           type=float, default=0.003,  help="Learning rate (default: 0.003 for fine-tune)")
    p.add_argument("--seq",          type=int,   default=25,     help="Sequence length (default: 25)")
    p.add_argument("--max-seqs",     type=int,   default=200,    help="Max sequences per epoch (default: 200)")
    p.add_argument("--save-every",   type=int,   default=5,      help="Save checkpoint every N epochs (default: 5)")
    p.add_argument("--output",       type=str,   default="base_model.npz", help="Output weights file")
    p.add_argument("--from-scratch", action="store_true", help="Train with fresh random weights (ignore existing model)")
    p.add_argument("--hidden",       type=int,   default=128,    help="Hidden size (must match base model — default: 128)")
    return p.parse_args()


# ─── Training loop ────────────────────────────────────────────────────────────

def train(model, text, epochs, lr, seq_length, max_seqs):
    """
    Full training loop with epoch tracking and loss reporting.
    Returns list of (epoch, loss) tuples.
    """
    # Encode entire corpus once
    encoded = model.one_hot_encoder.encode(text)
    total_chars = len(encoded)

    if total_chars < seq_length + 1:
        print(f"❌ Text too short ({total_chars} chars). Need at least {seq_length + 1}.")
        return []

    # Build all (input, target) sequence pairs
    X_all, y_all = [], []
    for i in range(total_chars - seq_length):
        X_all.append(encoded[i : i + seq_length])
        y_all.append(encoded[i + 1 : i + seq_length + 1])

    total_seqs = len(X_all)
    seqs_per_epoch = min(max_seqs, total_seqs)
    print(f"📚 Corpus: {total_chars:,} chars → {total_seqs:,} sequences "
          f"(using {seqs_per_epoch} per epoch)")
    print()

    history = []
    best_loss = float('inf')

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()

        # Shuffle and sample sequences each epoch
        indices = np.random.permutation(total_seqs)[:seqs_per_epoch]
        epoch_loss = 0.0

        for idx in indices:
            # Reset LSTM state for each sequence
            model.h = np.zeros((model.hidden_size, 1))
            model.c = np.zeros((model.hidden_size, 1))

            # Forward + backward
            model.forw_prop(X_all[idx])
            loss = model.back_prop(y_all[idx], learning_rate=lr)
            epoch_loss += loss

        avg_loss = epoch_loss / seqs_per_epoch
        elapsed = time.time() - epoch_start
        history.append((epoch, avg_loss))

        # Visual loss bar
        bar_len = 20
        if epoch == 1:
            first_loss = avg_loss
        normalized = min(avg_loss / (first_loss + 1e-8), 1.0)
        bar = "█" * int(normalized * bar_len) + "░" * (bar_len - int(normalized * bar_len))

        improved = " ← best" if avg_loss < best_loss else ""
        if avg_loss < best_loss:
            best_loss = avg_loss

        print(f"Epoch {epoch:>3}/{epochs}  loss: {avg_loss:.4f}  [{bar}]  ({elapsed:.1f}s){improved}")

    return history


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # ── Load training text ───────────────────────────────────────────────────
    if not os.path.exists(args.data):
        print(f"❌ File not found: {args.data}")
        return

    with open(args.data, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    # Filter to vocabulary
    filtered = "".join(c for c in raw_text if c in set(voc))
    skipped = len(raw_text) - len(filtered)
    print(f"📄 Loaded: {args.data}")
    print(f"   Total chars : {len(raw_text):,}")
    print(f"   In-vocab    : {len(filtered):,} ({len(filtered)/len(raw_text)*100:.1f}%)")
    if skipped > 0:
        print(f"   Skipped     : {skipped:,} chars not in vocabulary (emojis, special chars)")
    print()

    if len(filtered) < args.seq + 1:
        print(f"❌ Not enough in-vocabulary text to train (need > {args.seq} chars).")
        return

    # ── Initialize model ─────────────────────────────────────────────────────
    model = LSTM(voc, hidden_size=args.hidden)

    if args.from_scratch:
        print("🆕 Starting with fresh random weights")
    elif os.path.exists(args.output):
        try:
            model.load_weights(args.output)
            print(f"✅ Loaded existing weights from: {args.output}")
            print(f"   (fine-tuning from here with lr={args.lr})")
        except Exception as e:
            print(f"⚠️  Could not load weights ({e}) — starting fresh")
    else:
        print(f"⚠️  {args.output} not found — starting with fresh weights")

    print()
    print("─" * 60)
    print(f"  Training config:")
    print(f"  ├─ Epochs      : {args.epochs}")
    print(f"  ├─ Learning rate: {args.lr}")
    print(f"  ├─ Seq length  : {args.seq}")
    print(f"  ├─ Max seqs/ep : {args.max_seqs}")
    print(f"  └─ Output      : {args.output}")
    print("─" * 60)
    print()

    # ── Train ────────────────────────────────────────────────────────────────
    history = train(model, filtered, args.epochs, args.lr, args.seq, args.max_seqs)

    if not history:
        return

    # ── Save ─────────────────────────────────────────────────────────────────
    print()
    model.save_weights(args.output)
    print(f"✅ Weights saved → {args.output}")

    # Save checkpoint copy with timestamp
    ts = time.strftime("%Y%m%d_%H%M%S")
    ckpt = args.output.replace(".npz", f"_checkpoint_{ts}.npz")
    model.save_weights(ckpt)
    print(f"💾 Checkpoint  → {ckpt}")

    # ── Summary ──────────────────────────────────────────────────────────────
    first_loss = history[0][1]
    final_loss = history[-1][1]
    improvement = (first_loss - final_loss) / first_loss * 100 if first_loss > 0 else 0

    print()
    print("─" * 60)
    print(f"  Training complete!")
    print(f"  ├─ Start loss  : {first_loss:.4f}")
    print(f"  ├─ Final loss  : {final_loss:.4f}")
    print(f"  └─ Improvement : {improvement:.1f}%")
    print("─" * 60)

    if improvement > 5:
        print("🎉 Good improvement! Model is learning the new corpus.")
    elif improvement > 0:
        print("📈 Slight improvement. Try more epochs or a different learning rate.")
    else:
        print("⚠️  Loss didn't improve. Try: lower --lr, more --epochs, or check your data.")


if __name__ == "__main__":
    main()
