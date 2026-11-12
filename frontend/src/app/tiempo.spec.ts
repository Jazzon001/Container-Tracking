import { duracion, hace } from './tiempo';

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

describe('duracion', () => {
  const inicio = '2026-11-10T08:00:00Z';

  it('entre dos fechas, con las dos unidades más grandes', () => {
    expect(duracion(inicio, '2026-11-10T08:25:00Z', AHORA)).toBe('25 min');
    expect(duracion(inicio, '2026-11-10T11:10:00Z', AHORA)).toBe('3 h 10 min');
    expect(duracion(inicio, '2026-11-12T12:30:00Z', AHORA)).toBe('2 d 4 h');
  });

  it('si no ha terminado, cuenta hasta ahora', () => {
    expect(duracion('2026-11-12T09:00:00Z', null, AHORA)).toBe('3 h');
  });

  it('menos de un minuto no se muestra como cero', () => {
    expect(duracion(inicio, '2026-11-10T08:00:30Z', AHORA)).toBe('menos de 1 min');
  });

  it('un fin anterior al inicio (reloj desajustado) no da tiempo negativo', () => {
    expect(duracion(inicio, '2026-11-10T07:00:00Z', AHORA)).toBe('menos de 1 min');
  });
});
