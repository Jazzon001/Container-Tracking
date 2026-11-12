import { TestBed } from '@angular/core/testing';
import { ConexionService } from './conexion.service';

describe('ConexionService', () => {
  it('arranca con el estado de conexión del navegador', () => {
    expect(TestBed.inject(ConexionService).enLinea()).toBe(navigator.onLine);
  });

  it('avisa cuando se pierde la conexión', () => {
    const servicio = TestBed.inject(ConexionService);
    window.dispatchEvent(new Event('offline'));
    expect(servicio.enLinea()).toBe(false);
  });

  it('avisa cuando se recupera', () => {
    const servicio = TestBed.inject(ConexionService);
    window.dispatchEvent(new Event('offline'));
    window.dispatchEvent(new Event('online'));
    expect(servicio.enLinea()).toBe(true);
  });
});
