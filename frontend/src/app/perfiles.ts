import { TipoCarro } from './carro.model';

export type Rol =
  | 'poy'
  | 'almacen'
  | 'dty'
  | 'twisting'
  | 'admin'
  | 'digitador_poy'
  | 'intermedio_poy'
  | 'empacador_poy'
  | 'digitador_dty'
  | 'empacador_dty'
  | 'digitador_twt'
  | 'empacador_twt';

/** Lo que un perfil puede hacer con los carros de su proceso. */
export type Accion = 'cargar' | 'liberar' | 'mantener';

export interface Permisos {
  /** Proceso del que ve los carros; null = todos. */
  tipo: TipoCarro | null;
  cargar: boolean;
  liberar: boolean;
  mantener: boolean;
}

const COMPLETO = { cargar: true, liberar: true, mantener: true };
const SIN_CARGAR = { cargar: false, liberar: true, mantener: true };

/**
 * Qué puede hacer cada perfil. Sirve solo para mostrar u ocultar opciones: la tabla que manda
 * es la del servidor (backend/app/permisos.py), que valida cada petición. Si una cambia, la
 * otra también debe cambiar.
 */
export const PERMISOS: Record<Rol, Permisos> = {
  admin: { tipo: null, ...COMPLETO },
  // POY
  digitador_poy: { tipo: 'poy', ...COMPLETO },
  intermedio_poy: { tipo: 'poy', ...SIN_CARGAR },
  empacador_poy: { tipo: 'poy', ...SIN_CARGAR },
  // DTY (Twisting libera los carros de DTY: es quien consume su producto)
  digitador_dty: { tipo: 'dty', ...COMPLETO },
  empacador_dty: { tipo: 'dty', ...SIN_CARGAR },
  twisting: { tipo: 'dty', ...SIN_CARGAR },
  // Twisting
  digitador_twt: { tipo: 'twisting', ...COMPLETO },
  empacador_twt: { tipo: 'twisting', ...SIN_CARGAR },
  // Nombres anteriores: se conservan para no romper a los usuarios ya creados.
  poy: { tipo: 'poy', ...COMPLETO },
  dty: { tipo: 'dty', ...COMPLETO },
  almacen: { tipo: null, cargar: false, liberar: true, mantener: false },
};
