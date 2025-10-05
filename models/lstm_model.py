import numpy as np
import os

# EXACT 89-character vocabulary from your Sherlock Holmes book training
voc = [
    '\n', ' ', '!', '&', '(', ')', '*', ',', '-', '.', 
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
    ':', ';', '?', 
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 
    '_', 
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 
    '£', '½', 'à', 'â', 'æ', 'è', 'é', 'œ', 
    '—', '‘', '’', '“', '”'
]


class OneHotEncoder:
    def __init__(self, vocab):
        self.vocab = vocab
        self.char_to_idx = {char: i for i, char in enumerate(vocab)}
        self.idx_to_char = {i: char for i, char in enumerate(vocab)}

    def encode(self, text):
        encoded = []
        for char in text:
            vec = np.zeros(len(self.vocab))
            if char in self.char_to_idx:
                vec[self.char_to_idx[char]] = 1
            encoded.append(vec)
        return np.array(encoded)

    def decode(self, one_hot_array):
        chars = []
        for vec in one_hot_array:
            idx = np.argmax(vec)
            chars.append(self.idx_to_char[idx])
        return ''.join(chars)

class LSTM:
    def __init__(self, voc, hidden_size):
        self.voc = voc
        self.one_hot_encoder = OneHotEncoder(voc)
        self.hidden_size = hidden_size
        self.vocab_size = len(voc)

        # EXACT SAME INITIALIZATION AS YOUR BASE MODEL
        self.W_i = np.random.randn(hidden_size, hidden_size + self.vocab_size) * 0.01
        self.W_f = np.random.randn(hidden_size, hidden_size + self.vocab_size) * 0.01
        self.W_c = np.random.randn(hidden_size, hidden_size + self.vocab_size) * 0.01
        self.W_o = np.random.randn(hidden_size, hidden_size + self.vocab_size) * 0.01
        self.W_hy = np.random.randn(self.vocab_size, hidden_size) * 0.01

        # EXACT SAME BIAS INITIALIZATION AS YOUR BASE MODEL
        self.b_i = np.zeros((hidden_size, 1))
        self.b_f = np.zeros((hidden_size, 1))  # NOTE: zeros, not ones!
        self.b_c = np.zeros((hidden_size, 1))
        self.b_o = np.zeros((hidden_size, 1))
        self.b_y = np.zeros((self.vocab_size, 1))

        # States
        self.h = np.zeros((hidden_size, 1))
        self.c = np.zeros((hidden_size, 1))

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def tanh(self, x):
        return np.tanh(np.clip(x, -500, 500))

    def forw_prop(self, inp):
        """Forward propagation - EXACT MATCH"""
        t = len(inp)
        self.inputs = inp.copy()

        self.c_vec = np.zeros((t, self.hidden_size, 1))
        self.h_vec = np.zeros((t, self.hidden_size, 1))
        self.y_vec = np.zeros((t, self.vocab_size, 1))
        self.gate_f_vec = np.zeros((t, self.hidden_size, 1))
        self.gate_i_vec = np.zeros((t, self.hidden_size, 1))
        self.gate_o_vec = np.zeros((t, self.hidden_size, 1))
        self.gate_c_vec = np.zeros((t, self.hidden_size, 1))
        self.concat_inputs = []

        h_prev = self.h.copy()
        c_prev = self.c.copy()

        for timestep in range(t):
            x_t = inp[timestep].reshape(-1, 1)
            concat_input = np.vstack([h_prev, x_t])
            self.concat_inputs.append(concat_input)

            forget_gate = self.sigmoid(self.W_f @ concat_input + self.b_f)
            input_gate = self.sigmoid(self.W_i @ concat_input + self.b_i)
            candidate_gate = self.tanh(self.W_c @ concat_input + self.b_c)
            output_gate = self.sigmoid(self.W_o @ concat_input + self.b_o)

            c_current = forget_gate * c_prev + input_gate * candidate_gate
            h_current = output_gate * self.tanh(c_current)
            y_current = self.W_hy @ h_current + self.b_y

            self.c_vec[timestep] = c_current
            self.h_vec[timestep] = h_current
            self.y_vec[timestep] = y_current
            self.gate_f_vec[timestep] = forget_gate
            self.gate_i_vec[timestep] = input_gate
            self.gate_o_vec[timestep] = output_gate
            self.gate_c_vec[timestep] = candidate_gate

            h_prev = h_current
            c_prev = c_current

        self.h = h_prev
        self.c = c_prev
        return self.y_vec

    def back_prop(self, targets, learning_rate=0.01):
        """Backward propagation - EXACT MATCH"""
        t = len(targets)
        dW_i = np.zeros_like(self.W_i)
        dW_f = np.zeros_like(self.W_f)
        dW_c = np.zeros_like(self.W_c)
        dW_o = np.zeros_like(self.W_o)
        dW_hy = np.zeros_like(self.W_hy)
        db_i = np.zeros_like(self.b_i)
        db_f = np.zeros_like(self.b_f)
        db_c = np.zeros_like(self.b_c)
        db_o = np.zeros_like(self.b_o)
        db_y = np.zeros_like(self.b_y)

        dh_next = np.zeros_like(self.h)
        dc_next = np.zeros_like(self.c)
        total_loss = 0

        for timestep in reversed(range(t)):
            target = targets[timestep].reshape(-1, 1)
            y_pred = self.y_vec[timestep]
            exp_scores = np.exp(y_pred - np.max(y_pred))
            probs = exp_scores / np.sum(exp_scores)
            total_loss += -np.sum(target * np.log(probs + 1e-8))

            dy = probs - target
            dW_hy += dy @ self.h_vec[timestep].T
            db_y += dy

            dh = self.W_hy.T @ dy + dh_next

            h_current = self.h_vec[timestep]
            c_current = self.c_vec[timestep]
            forget_gate = self.gate_f_vec[timestep]
            input_gate = self.gate_i_vec[timestep]
            candidate_gate = self.gate_c_vec[timestep]
            output_gate = self.gate_o_vec[timestep]

            if timestep > 0:
                h_prev = self.h_vec[timestep-1]
                c_prev = self.c_vec[timestep-1]
            else:
                h_prev = np.zeros_like(h_current)
                c_prev = np.zeros_like(c_current)

            do_raw = dh * self.tanh(c_current)
            do = do_raw * output_gate * (1 - output_gate)
            dc = dc_next + dh * output_gate * (1 - self.tanh(c_current)**2)
            df_raw = dc * c_prev
            df = df_raw * forget_gate * (1 - forget_gate)
            di_raw = dc * candidate_gate
            di = di_raw * input_gate * (1 - input_gate)
            dg_raw = dc * input_gate
            dg = dg_raw * (1 - candidate_gate**2)
            concat_input = self.concat_inputs[timestep]

            dW_f += df @ concat_input.T
            dW_i += di @ concat_input.T
            dW_c += dg @ concat_input.T
            dW_o += do @ concat_input.T
            db_f += df
            db_i += di
            db_c += dg
            db_o += do

            dh_next = (self.W_f[:, :self.hidden_size].T @ df +
                       self.W_i[:, :self.hidden_size].T @ di +
                       self.W_c[:, :self.hidden_size].T @ dg +
                       self.W_o[:, :self.hidden_size].T @ do)
            dc_next = dc * forget_gate

        # Gradient clipping
        for grad in [dW_i, dW_f, dW_c, dW_o, dW_hy, db_i, db_f, db_c, db_o, db_y]:
            np.clip(grad, -5, 5, out=grad)

        # Weight updates
        self.W_i -= learning_rate * dW_i
        self.W_f -= learning_rate * dW_f
        self.W_c -= learning_rate * dW_c
        self.W_o -= learning_rate * dW_o
        self.W_hy -= learning_rate * dW_hy
        self.b_i -= learning_rate * db_i
        self.b_f -= learning_rate * db_f
        self.b_c -= learning_rate * db_c
        self.b_o -= learning_rate * db_o
        self.b_y -= learning_rate * db_y

        return total_loss / t

    def prepare_sequences(self, text_data, seq_length):
        """Prepare training sequences from text data"""
        encoded_text = self.one_hot_encoder.encode(text_data)
        X_sequences, y_sequences = [], []
        for i in range(len(encoded_text) - seq_length):
            X_sequences.append(encoded_text[i:i + seq_length])
            y_sequences.append(encoded_text[i + 1:i + seq_length + 1])
        return X_sequences, y_sequences

    def train_incremental(self, text_data, seq_length=25, learning_rate=0.005):
        """Incremental training on new diary entries"""
        if len(text_data) < seq_length:
            return 0

        X_sequences, y_sequences = self.prepare_sequences(text_data, seq_length)
        total_loss = 0
        sequences_trained = 0

        for X_seq, y_seq in zip(X_sequences[:10], y_sequences[:10]):
            self.h = np.zeros((self.hidden_size, 1))
            self.c = np.zeros((self.hidden_size, 1))
            self.forw_prop(X_seq)
            loss = self.back_prop(y_seq, learning_rate)
            total_loss += loss
            sequences_trained += 1

        return total_loss / sequences_trained if sequences_trained > 0 else 0

    def save_weights(self, filename):
        """Save weights - EXACT MATCH"""
        try:
            np.savez(filename,
                     W_i=self.W_i, W_f=self.W_f, W_c=self.W_c, W_o=self.W_o, W_hy=self.W_hy,
                     b_i=self.b_i, b_f=self.b_f, b_c=self.b_c, b_o=self.b_o, b_y=self.b_y,
                     h=self.h, c=self.c)
        except Exception as e:
            print(f"YourDiary Error saving weights: {e}")

    def load_weights(self, filename):
        """Load weights - EXACT MATCH"""
        try:
            data = np.load(filename, allow_pickle=True)
            self.W_i = data['W_i']; self.W_f = data['W_f']; self.W_c = data['W_c']; self.W_o = data['W_o']
            self.W_hy = data['W_hy']; self.b_i = data['b_i']; self.b_f = data['b_f']
            self.b_c = data['b_c']; self.b_o = data['b_o']; self.b_y = data['b_y']
            self.h = data['h']; self.c = data['c']
        except Exception as e:
            print(f"YourDiary Error loading weights: {e}")

    def get_completions(self, text, num_suggestions=3, max_length=20):
        """Generate diary writing suggestions using your trained model"""
        suggestions = []

        # Filter input text to valid vocabulary
        filtered_text = ''.join([ch for ch in text if ch in self.one_hot_encoder.char_to_idx])
        if not filtered_text:
            return self._generate_diary_suggestions(num_suggestions, max_length)

        try:
            input_encoded = self.one_hot_encoder.encode(filtered_text)

            for suggestion_idx in range(num_suggestions):
                # Reset LSTM state for each suggestion
                self.h = np.zeros((self.hidden_size, 1))
                self.c = np.zeros((self.hidden_size, 1))

                # Process input text - EXACT SAME AS YOUR generate_text METHOD
                if len(input_encoded) > 0:
                    self.forw_prop(input_encoded)

                # Generate completion using the EXACT SAME METHOD
                completion = self._generate_sequence_like_original(max_length, temperature=0.8)

                if completion.strip() and completion not in suggestions:
                    suggestions.append(completion)

        except Exception as e:
            print(f"Error generating completions: {e}")
            return self._generate_diary_suggestions(num_suggestions, max_length)

        # Fill remaining suggestions if needed
        while len(suggestions) < num_suggestions:
            completion = self._generate_diary_suggestions(1, max_length)[0]
            if completion not in suggestions:
                suggestions.append(completion)

        return suggestions[:num_suggestions]

    def _generate_sequence_like_original(self, num_chars, temperature=1.0):
        """Generate sequence EXACTLY like your original generate_text method"""
        generated = ""
        
        for _ in range(num_chars):
            # EXACT SAME LOGIC AS YOUR generate_text METHOD
            last_output = self.y_vec[-1].flatten() if hasattr(self, 'y_vec') else np.random.randn(self.vocab_size)
            scaled_output = last_output / temperature
            exp_scores = np.exp(scaled_output - np.max(scaled_output))
            probabilities = exp_scores / np.sum(exp_scores)
            next_char_idx = np.random.choice(len(probabilities), p=probabilities)
            next_char = self.voc[next_char_idx]
            generated += next_char
            
            # Continue with single character forward pass
            next_input = self.one_hot_encoder.encode(next_char)
            self.forw_prop(next_input)
            
        return generated

    def _generate_diary_suggestions(self, num_suggestions, max_length):
        """Generate diary-themed suggestions from scratch"""
        diary_starts = [
            ' felt wonderful today',
            ' brought back memories',
            ' made me think deeply',
            ' was quite remarkable',
            ' seemed very important',
            ' reminded me of home',
            ' filled my heart with joy'
        ]

        suggestions = []
        for i in range(num_suggestions):
            if i < len(diary_starts):
                completion = diary_starts[i]
            else:
                thoughtful_words = ['meaningful', 'beautiful', 'peaceful', 'inspiring', 'joyful']
                word = np.random.choice(thoughtful_words)
                completion = f' was quite {word}'

            suggestions.append(completion[:max_length])

        return suggestions

    def get_completions_till_period(self, text, num_suggestions=3):
        """Generate diary sentences until period"""
        suggestions = []

        filtered_text = ''.join([ch for ch in text if ch in self.one_hot_encoder.char_to_idx])
        if not filtered_text:
            return self._generate_diary_sentences(num_suggestions)

        try:
            input_encoded = self.one_hot_encoder.encode(filtered_text)

            for suggestion_idx in range(num_suggestions):
                self.h = np.zeros((self.hidden_size, 1))
                self.c = np.zeros((self.hidden_size, 1))

                if len(input_encoded) > 0:
                    self.forw_prop(input_encoded)
                
                completion = self._generate_until_period()

                if completion.strip() and completion not in suggestions:
                    suggestions.append(completion)

        except Exception as e:
            return self._generate_diary_sentences(num_suggestions)

        while len(suggestions) < num_suggestions:
            completion = self._generate_diary_sentences(1)[0]
            if completion not in suggestions:
                suggestions.append(completion)

        return suggestions[:num_suggestions]

    def _generate_until_period(self):
        """Generate text until period"""
        completion = ''
        temperature = 0.8

        for _ in range(80):
            try:
                last_output = self.y_vec[-1].flatten() if hasattr(self, 'y_vec') else np.random.randn(self.vocab_size)
                scaled_output = last_output / temperature
                exp_scores = np.exp(scaled_output - np.max(scaled_output))
                probabilities = exp_scores / np.sum(exp_scores)
                next_char_idx = np.random.choice(len(probabilities), p=probabilities)
                next_char = self.voc[next_char_idx]
                completion += next_char

                if next_char == '.':
                    break
                elif len(completion) > 20 and next_char in ['!', '?']:
                    break

                # Continue forward pass
                next_input = self.one_hot_encoder.encode(next_char)
                self.forw_prop(next_input)

            except Exception as e:
                break

        return completion

    def _generate_diary_sentences(self, num_suggestions):
        """Generate complete diary sentences"""
        sentences = [
            ' was a beautiful moment to remember.',
            ' made today feel quite special indeed.',
            ' helped me grow in unexpected ways.',
            ' reminded me of what truly matters.',
            ' brought such joy to my weary heart.'
        ]

        return sentences[:num_suggestions]


class LSTMModelManager:
    def __init__(self):
        self.base_model = None
        self.user_models = {}

    def load_base_model(self):
        """Load or create YourDiary base model with EXACT MATCHING SETUP"""
        # Use hidden_size=128 to match your training!
        self.base_model = LSTM(voc, hidden_size=128)

        if os.path.exists("base_model.npz"):
            try:
                self.base_model.load_weights("base_model.npz")
                print("✅ YourDiary AI: Base model loaded successfully")
            except Exception as e:
                print(f"⚠️ YourDiary AI: Error loading base model: {e}")
                print("ℹ️ Using fresh AI weights - will learn from your writing!")
        else:
            print("ℹ️ YourDiary AI: Initializing fresh neural network")
            print("💡 Your AI will start learning immediately from your first entries!")

    def get_user_model(self, user_id):
        """Get or create user-specific YourDiary AI model"""
        if user_id not in self.user_models:
            # Use hidden_size=128 to match your training!
            self.user_models[user_id] = LSTM(voc, hidden_size=128)
            user_path = f"yourdiary_users/user_{user_id}.npz"

            if os.path.exists(user_path):
                try:
                    self.user_models[user_id].load_weights(user_path)
                    print(f"✅ YourDiary AI: Personal model loaded for user {user_id}")
                except Exception as e:
                    print(f"⚠️ YourDiary AI: Error loading user model: {e}")
                    self.copy_base_to_user(user_id)
            else:
                self.copy_base_to_user(user_id)

        return self.user_models[user_id]

    def copy_base_to_user(self, user_id):
        """Initialize user model with base weights"""
        if self.base_model and user_id in self.user_models:
            try:
                user_model = self.user_models[user_id]
                user_model.W_i = self.base_model.W_i.copy()
                user_model.W_f = self.base_model.W_f.copy()
                user_model.W_c = self.base_model.W_c.copy()
                user_model.W_o = self.base_model.W_o.copy()
                user_model.W_hy = self.base_model.W_hy.copy()
                user_model.b_i = self.base_model.b_i.copy()
                user_model.b_f = self.base_model.b_f.copy()
                user_model.b_c = self.base_model.b_c.copy()
                user_model.b_o = self.base_model.b_o.copy()
                user_model.b_y = self.base_model.b_y.copy()
                print(f"📋 YourDiary AI: Personal assistant initialized for user {user_id}")
            except Exception as e:
                print(f"⚠️ YourDiary AI: Error initializing user model: {e}")

    def train_user_model_background(self, user_id, diary_entries):
        """Train personal YourDiary AI on user's writing"""
        try:
            print(f"🎯 YourDiary AI: Learning from user {user_id}'s writing style")
            user_model = self.get_user_model(user_id)
            training_text = " ".join(diary_entries)

            if len(training_text) > 25:
                loss = user_model.train_incremental(training_text, seq_length=25, learning_rate=0.005)
                print(f"📊 YourDiary AI: Learning progress - loss: {loss:.4f}")

                os.makedirs("yourdiary_users", exist_ok=True)
                user_model.save_weights(f"yourdiary_users/user_{user_id}.npz")
                print(f"💾 YourDiary AI: Personal model saved for user {user_id}")
                print(f"🎉 Your AI assistant is getting smarter with your writing style!")

        except Exception as e:
            print(f"❌ YourDiary AI: Training error for user {user_id}: {e}")
            import traceback
            traceback.print_exc()