from jax import config
config.update("jax_enable_x64", True) #important -> else aaa fails
import jax.numpy as np
import jax

def check_inputs(z_k, f_k):
  f_k = np.array(f_k)
  z_k = np.array(z_k)

  if z_k.ndim != 1:
    raise ValueError("z_k should be 1D but has shape {z_k.shape}")
  M = z_k.shape[0]

  if f_k.ndim == 1:
    f_k = f_k[:, np.newaxis]

  if f_k.ndim != 2 or f_k.shape[0]!=M:
    raise ValueError("f_k should be 1 or 2D and have the same first"
                     f"dimension as z_k, {f_k.shape=}, {z_k.shape=}")
  V = f_k.shape[1]

  return z_k, f_k, M, V

def vectorial_aaa(z_k, f_k, tol=1e-13, mmax=100):
  """Compute a rational approximation of `F` over the points `Z` using the
  AAA algorithm.

  Arguments:
      Z (array (M,)): M sample points
      F (array (M, V)): vector valued function values
      tol: the approximation tolerance
      mmax: the maximum number of iterations/degree of the resulting approximant

  Returns:

  """
  z_k, f_k, M, V = check_inputs(z_k, f_k)

  J = np.ones(M, dtype=bool)
  z_j = np.empty(0, dtype=z_k.dtype)
  f_j = np.empty((0, V), dtype=f_k.dtype)
  errors = []

  reltol = tol * np.linalg.norm(f_k, np.inf)

  r_k = np.mean(f_k) * np.ones_like(f_k)

  for m in range(mmax):
      # find largest residual
      jj = np.argmax(np.linalg.norm(f_k - r_k, axis=-1)) #Next sample point to include
      z_j = np.append(z_j, np.array([z_k[jj]]))
      f_j = np.concatenate([f_j, f_k[jj][None, :]])
      J = J.at[jj].set(False)

      # Cauchy matrix containing the basis functions as columns
      C = 1.0 / (z_k[J,None] - z_j[None,:])
      # Loewner matrix
      A = (f_k[J,None] - f_j[None,:]) * C[:,:,None]

      # TODO: stack A
      A = np.concatenate(np.moveaxis(A, -1, 0))

      # compute weights as right singular vector for smallest singular value
      _, _, Vh = np.linalg.svd(A)

      w_j = Vh[-1, :].conj()

      # approximation: numerator / denominator
      N = C.dot(w_j[:, None] * f_j) #TODO check it works
      D = C.dot(w_j)[:, None]

      # update residual
      r_k = f_k.at[J].set(N / D)

      # check for convergence
      errors.append(np.linalg.norm(f_k - r_k, np.inf))
      if errors[-1] <= reltol:
          break

  return z_j, f_j, w_j
