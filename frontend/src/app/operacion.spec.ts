import { Subject, of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Operacion } from './operacion';

describe('Operacion', () => {
  let operacion: Operacion;

  beforeEach(() => (operacion = new Operacion()));

  it('arranca sin mensajes y sin enviar', () => {
    expect(operacion.mensaje()).toBe('');
    expect(operacion.error()).toBe('');
    expect(operacion.enviando()).toBe(false);
  });

  it('mientras espera la respuesta está enviando y no muestra mensajes', () => {
    operacion.ejecutar(new Subject<string>(), () => 'listo', 'falló');
    expect(operacion.enviando()).toBe(true);
    expect(operacion.mensaje()).toBe('');
  });

  it('al tener éxito muestra el mensaje, deja de enviar y avisa que terminó bien', () => {
    const alTerminarBien = vi.fn();
    operacion.ejecutar(of('C-001'), (carro) => `Carro ${carro} listo`, 'falló', alTerminarBien);

    expect(operacion.mensaje()).toBe('Carro C-001 listo');
    expect(operacion.enviando()).toBe(false);
    expect(alTerminarBien).toHaveBeenCalledTimes(1);
  });

  it('al fallar muestra el mensaje de la API y no avisa que terminó bien', () => {
    const alTerminarBien = vi.fn();
    const fallo = { status: 409, error: { detail: 'El carro no está disponible' } };
    operacion.ejecutar(throwError(() => fallo), () => 'listo', 'falló', alTerminarBien);

    expect(operacion.error()).toBe('El carro no está disponible');
    expect(operacion.mensaje()).toBe('');
    expect(operacion.enviando()).toBe(false);
    expect(alTerminarBien).not.toHaveBeenCalled();
  });

  it('usa el texto de respaldo si la API no explica el fallo', () => {
    operacion.ejecutar(throwError(() => ({ status: 500 })), () => 'listo', 'No se pudo cargar el carro');
    expect(operacion.error()).toBe('No se pudo cargar el carro');
  });

  it('borra el resultado anterior al empezar otra operación', () => {
    operacion.ejecutar(of('x'), () => 'primero', 'falló');
    operacion.ejecutar(new Subject<string>(), () => 'segundo', 'falló');
    expect(operacion.mensaje()).toBe('');

    operacion.ejecutar(throwError(() => ({ status: 500 })), () => 'tercero', 'falló');
    operacion.ejecutar(new Subject<string>(), () => 'cuarto', 'falló');
    expect(operacion.error()).toBe('');
  });

  describe('fallar', () => {
    it('muestra el error y quita el mensaje de éxito anterior', () => {
      operacion.ejecutar(of('x'), () => 'hecho', 'falló');
      operacion.fallar('Falta el número');

      expect(operacion.error()).toBe('Falta el número');
      expect(operacion.mensaje()).toBe('');
    });
  });
});
