import { afterEach, vi } from 'vitest';
import { olvidarDatosEnCache } from './cache-offline';

describe('olvidarDatosEnCache', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('borra las cachés de datos de la API y deja las de la aplicación', async () => {
    const borrar = vi.fn().mockResolvedValue(true);
    vi.stubGlobal('caches', {
      keys: vi.fn().mockResolvedValue(['carros-datos-v1', 'carros-app-v1']),
      delete: borrar,
    });

    await olvidarDatosEnCache();

    expect(borrar).toHaveBeenCalledTimes(1);
    expect(borrar).toHaveBeenCalledWith('carros-datos-v1');
  });

  it('no hace nada si no hay cachés de datos', async () => {
    const borrar = vi.fn();
    vi.stubGlobal('caches', { keys: vi.fn().mockResolvedValue(['carros-app-v1']), delete: borrar });

    await olvidarDatosEnCache();

    expect(borrar).not.toHaveBeenCalled();
  });

  it('no falla si el navegador no tiene caché', async () => {
    vi.stubGlobal('caches', undefined);
    await expect(olvidarDatosEnCache()).resolves.toBeUndefined();
  });

  it('no falla si la caché lanza un error', async () => {
    vi.stubGlobal('caches', { keys: vi.fn().mockRejectedValue(new Error('sin acceso')), delete: vi.fn() });
    await expect(olvidarDatosEnCache()).resolves.toBeUndefined();
  });
});
