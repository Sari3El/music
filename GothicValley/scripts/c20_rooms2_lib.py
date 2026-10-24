import numpy as np


def max_rect(M):
    """Largest all-True axis-aligned rectangle in a 2-D boolean grid -> (i0, i1, j0, j1) half-open."""
    best = (0, 0, 0, 0, 0); h = np.zeros(M.shape[1], int)
    for i in range(M.shape[0]):
        h = np.where(M[i], h + 1, 0)
        st = []
        for j in range(M.shape[1] + 1):
            cur = h[j] if j < M.shape[1] else 0
            start = j
            while st and st[-1][1] >= cur:
                s_, hh = st.pop()
                area = hh * (j - s_)
                if area > best[0]:
                    best = (area, i - hh + 1, i + 1, s_, j)
                start = s_
            st.append((start, cur))
    return best[1:]
