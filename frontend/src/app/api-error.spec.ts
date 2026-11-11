import { mensajeDeApi } from './api-error';

describe('mensajeDeApi', () => {
  it('usa el mensaje que envía la API', () => {
    const fallo = { status: 409, error: { detail: 'El carro no está disponible para cargarse' } };
    expect(mensajeDeApi(fallo, 'Error')).toBe('El carro no está disponible para cargarse');
  });

  it('avisa de falta de conexión cuando no hay respuesta', () => {
    expect(mensajeDeApi({ status: 0 }, 'Error')).toContain('No se pudo conectar');
  });

  it('usa el texto por defecto si el detalle no es un texto (por ejemplo, un 422)', () => {
    const fallo = { status: 422, error: { detail: [{ msg: 'campo requerido' }] } };
    expect(mensajeDeApi(fallo, 'No se pudo cargar el carro')).toBe('No se pudo cargar el carro');
  });

  it('usa el texto por defecto si no hay detalle', () => {
    expect(mensajeDeApi({ status: 500 }, 'Error del servidor')).toBe('Error del servidor');
  });

  it('muestra el mensaje de un error propio de la aplicación', () => {
    expect(mensajeDeApi(new Error('No existe un carro con el número C-9'), 'Error')).toBe(
      'No existe un carro con el número C-9',
    );
  });

  it('no falla con valores inesperados', () => {
    expect(mensajeDeApi(null, 'Error')).toBe('Error');
    expect(mensajeDeApi(undefined, 'Error')).toBe('Error');
  });
});
