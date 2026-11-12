import { COOKIE_DE_SESION, marcarSesionCerrada, marcarSesionIniciada } from './sesion-cookie';

const hayCookie = () => document.cookie.split('; ').some((c) => c.startsWith(`${COOKIE_DE_SESION}=1`));

describe('cookie de sesión', () => {
  afterEach(() => marcarSesionCerrada());

  it('se crea al iniciar sesión', () => {
    marcarSesionIniciada();
    expect(hayCookie()).toBe(true);
  });

  it('se borra al cerrar sesión', () => {
    marcarSesionIniciada();
    marcarSesionCerrada();
    expect(hayCookie()).toBe(false);
  });

  it('cerrar sesión sin haberla iniciado no falla', () => {
    expect(() => marcarSesionCerrada()).not.toThrow();
    expect(hayCookie()).toBe(false);
  });

  it('no guarda nada sensible: solo una marca', () => {
    marcarSesionIniciada();
    const cookie = document.cookie.split('; ').find((c) => c.startsWith(COOKIE_DE_SESION));
    expect(cookie).toBe(`${COOKIE_DE_SESION}=1`);
  });
});
