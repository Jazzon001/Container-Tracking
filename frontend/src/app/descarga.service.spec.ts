import { TestBed } from '@angular/core/testing';
import { afterEach, vi } from 'vitest';
import { DescargaService } from './descarga.service';

describe('DescargaService', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('descarga el contenido con el nombre indicado y suelta la dirección temporal', () => {
    const crear = vi.fn().mockReturnValue('blob:temporal');
    const soltar = vi.fn();
    vi.stubGlobal('URL', { createObjectURL: crear, revokeObjectURL: soltar });
    let enlace: HTMLAnchorElement | undefined;
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      enlace = this;
    });
    const contenido = new Blob(['xlsx']);

    TestBed.inject(DescargaService).guardar(contenido, 'reporte.xlsx');

    expect(crear).toHaveBeenCalledWith(contenido);
    expect(enlace?.download).toBe('reporte.xlsx');
    expect(enlace?.href).toContain('blob:temporal');
    expect(soltar).toHaveBeenCalledWith('blob:temporal');
  });
});
