"""CNN kecil murni NumPy (tanpa PyTorch/TensorFlow) dengan backprop manual.

Arsitektur:  Conv3x3(F) -> ReLU -> MaxPool2 -> Conv3x3(F) -> ReLU -> MaxPool2
             -> Flatten -> Dense(32) -> ReLU -> Dense(4) -> Softmax
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


class Conv3x3:
    def __init__(self, cin, cout, rng):
        self.W = rng.normal(0, np.sqrt(2 / (cin * 9)), (cout, cin * 9)).astype(np.float32)
        self.b = np.zeros(cout, np.float32)

    def forward(self, x):
        N, C, H, W = x.shape
        xp = np.pad(x, ((0, 0), (0, 0), (1, 1), (1, 1)))
        win = sliding_window_view(xp, (3, 3), axis=(2, 3))          # N,C,H,W,3,3
        cols = win.transpose(0, 2, 3, 1, 4, 5).reshape(N * H * W, C * 9)
        out = cols @ self.W.T + self.b                               # NHW,F
        self.cache = (cols, x.shape)
        return out.reshape(N, H, W, -1).transpose(0, 3, 1, 2)

    def backward(self, dout):
        cols, (N, C, H, W) = self.cache
        d = dout.transpose(0, 2, 3, 1).reshape(N * H * W, -1)
        self.dW, self.db = d.T @ cols, d.sum(0)
        dcols = (d @ self.W).reshape(N, H, W, C, 3, 3)
        dxp = np.zeros((N, C, H + 2, W + 2), np.float32)
        for i in range(3):
            for j in range(3):
                dxp[:, :, i:i + H, j:j + W] += dcols[:, :, :, :, i, j].transpose(0, 3, 1, 2)
        return dxp[:, :, 1:-1, 1:-1]

    params = property(lambda s: [(s.W, "dW"), (s.b, "db")])


class MaxPool2:
    def forward(self, x):
        N, C, H, W = x.shape
        xr = x.reshape(N, C, H // 2, 2, W // 2, 2)
        out = xr.max(axis=(3, 5))
        self.mask = xr == out[:, :, :, None, :, None]
        self.shape = x.shape
        return out

    def backward(self, dout):
        m = self.mask / self.mask.sum(axis=(3, 5), keepdims=True)    # bagi rata bila seri
        dx = m * dout[:, :, :, None, :, None]
        return dx.reshape(self.shape)


class ReLU:
    def forward(self, x):
        self.m = x > 0
        return x * self.m

    def backward(self, d):
        return d * self.m


class Dense:
    def __init__(self, nin, nout, rng):
        self.W = rng.normal(0, np.sqrt(2 / nin), (nin, nout)).astype(np.float32)
        self.b = np.zeros(nout, np.float32)

    def forward(self, x):
        self.x = x
        return x @ self.W + self.b

    def backward(self, d):
        self.dW, self.db = self.x.T @ d, d.sum(0)
        return d @ self.W.T

    params = property(lambda s: [(s.W, "dW"), (s.b, "db")])


class Flatten:
    def forward(self, x):
        self.shape = x.shape
        return x.reshape(len(x), -1)

    def backward(self, d):
        return d.reshape(self.shape)


class CNN:
    def __init__(self, in_ch, n_classes=4, filters=8, size=16, seed=0):
        rng = np.random.default_rng(seed)
        flat = filters * (size // 4) ** 2
        self.layers = [
            Conv3x3(in_ch, filters, rng), ReLU(), MaxPool2(),
            Conv3x3(filters, filters, rng), ReLU(), MaxPool2(),
            Flatten(), Dense(flat, 32, rng), ReLU(), Dense(32, n_classes, rng),
        ]
        self.opt = None

    def forward(self, x):
        for l in self.layers:
            x = l.forward(x)
        return x

    def predict_proba(self, x, bs=256):
        out = np.concatenate([self.forward(x[i:i + bs]) for i in range(0, len(x), bs)])
        e = np.exp(out - out.max(1, keepdims=True))
        return e / e.sum(1, keepdims=True)

    def predict(self, x):
        return self.predict_proba(x).argmax(1)

    def _adam(self, lr, b1=0.9, b2=0.999, eps=1e-8):
        params = [(l, p, g) for l in self.layers if hasattr(l, "params") for p, g in l.params]
        if self.opt is None:
            self.opt = {"t": 0, "m": [np.zeros_like(p) for _, p, _ in params],
                        "v": [np.zeros_like(p) for _, p, _ in params]}
        o = self.opt
        o["t"] += 1
        for k, (l, p, g) in enumerate(params):
            grad = getattr(l, g)
            o["m"][k] = b1 * o["m"][k] + (1 - b1) * grad
            o["v"][k] = b2 * o["v"][k] + (1 - b2) * grad ** 2
            mh = o["m"][k] / (1 - b1 ** o["t"])
            vh = o["v"][k] / (1 - b2 ** o["t"])
            p -= lr * mh / (np.sqrt(vh) + eps)

    def fit(self, X, y, epochs=12, bs=64, lr=2e-3, seed=0, verbose=True):
        rng = np.random.default_rng(seed)
        hist = []
        for ep in range(epochs):
            idx = rng.permutation(len(X))
            loss_sum = 0.0
            for i in range(0, len(X), bs):
                b = idx[i:i + bs]
                logits = self.forward(X[b])
                e = np.exp(logits - logits.max(1, keepdims=True))
                p = e / e.sum(1, keepdims=True)
                loss_sum += -np.log(p[np.arange(len(b)), y[b]] + 1e-9).sum()
                d = p.copy()
                d[np.arange(len(b)), y[b]] -= 1
                d /= len(b)
                for l in reversed(self.layers):
                    d = l.backward(d)
                self._adam(lr)
            hist.append(loss_sum / len(X))
            if verbose:
                print(f"  epoch {ep + 1:2d}/{epochs}  loss={hist[-1]:.4f}")
        return hist
