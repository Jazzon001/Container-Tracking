import { PERMISOS, Rol } from './perfiles';

// Esta tabla es la especificación de los perfiles, escrita a mano: si alguien cambia
// perfiles.ts sin querer, falla aquí. Debe coincidir con backend/test/test_permisos.py.
//                       proceso      cargar liberar mantener
const ESPERADO: Record<Rol, [string | null, boolean, boolean, boolean]> = {
  admin: [null, true, true, true],
  digitador_poy: ['poy', true, true, true],
  intermedio_poy: ['poy', false, true, true],
  empacador_poy: ['poy', false, true, true],
  digitador_dty: ['dty', true, true, true],
  empacador_dty: ['dty', false, true, true],
  twisting: ['dty', false, true, true],
  digitador_twt: ['twisting', true, true, true],
  empacador_twt: ['twisting', false, true, true],
  poy: ['poy', true, true, true],
  dty: ['dty', true, true, true],
  almacen: [null, false, true, false],
};

describe('PERMISOS', () => {
  it.each(Object.entries(ESPERADO))('%s', (rol, [tipo, cargar, liberar, mantener]) => {
    expect(PERMISOS[rol as Rol]).toEqual({ tipo, cargar, liberar, mantener });
  });

  it('solo los digitadores (y el administrador) pueden cargar', () => {
    const quienCarga = Object.entries(PERMISOS)
      .filter(([, permisos]) => permisos.cargar)
      .map(([rol]) => rol)
      .sort();
    expect(quienCarga).toEqual(
      ['admin', 'digitador_dty', 'digitador_poy', 'digitador_twt', 'dty', 'poy'].sort(),
    );
  });
});
