import { hace } from './tiempo';

const AHORA = Date.parse('2026-11-12T12:00:00Z');
const desde = (milisegundos: number) => new Date(AHORA - milisegundos).toISOString();
const MIN = 60_000;
const H = 60 * MIN;
const D = 24 * H;

describe('hace', () => {
  it('menos de un minuto: "hace instantes"', () => {
    expect(hace(desde(0), AHORA)).toBe('hace instantes');
    expect(hace(desde(59_000), AHORA)).toBe('hace instantes');
  });

  it('minutos', () => {
    expect(hace(desde(MIN), AHORA)).toBe('hace 1 min');
    expect(hace(desde(25 * MIN), AHORA)).toBe('hace 25 min');
    expect(hace(desde(59 * MIN + 59_000), AHORA)).toBe('hace 59 min');
  });

  it('horas, con minutos si sobran', () => {
    expect(hace(desde(H), AHORA)).toBe('hace 1 h');
    expect(hace(desde(3 * H + 10 * MIN), AHORA)).toBe('hace 3 h 10 min');
    expect(hace(desde(23 * H + 59 * MIN), AHORA)).toBe('hace 23 h 59 min');
  });

  it('días, con horas si sobran', () => {
    expect(hace(desde(D), AHORA)).toBe('hace 1 d');
    expect(hace(desde(2 * D + 4 * H + 30 * MIN), AHORA)).toBe('hace 2 d 4 h');
    expect(hace(desde(10 * D), AHORA)).toBe('hace 10 d');
  });

  it('una fecha en el futuro (reloj atrasado) no muestra tiempo negativo', () => {
    expect(hace(desde(-5 * MIN), AHORA)).toBe('hace instantes');
  });

  it('entiende las fechas UTC que envía la API', () => {
    expect(hace('2026-11-12T09:00:00Z', AHORA)).toBe('hace 3 h');
  });
});
