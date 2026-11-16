import { Routes } from '@angular/router';
import { authGuard, permisoGuard } from './auth.guard';
import { CargaComponent } from './carga.component';
import { CarrosComponent } from './carros.component';
import { EntregaComponent } from './entrega.component';
import { HistorialComponent } from './historial.component';
import { LoginComponent } from './login.component';
import { MantenimientoComponent } from './mantenimiento.component';
import { ReporteComponent } from './reporte.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'carros', component: CarrosComponent, canActivate: [authGuard] },
  { path: 'carga', component: CargaComponent, canActivate: [authGuard, permisoGuard('cargar')] },
  { path: 'entrega', component: EntregaComponent, canActivate: [authGuard, permisoGuard('liberar')] },
  {
    path: 'mantenimiento',
    component: MantenimientoComponent,
    canActivate: [authGuard, permisoGuard('mantener')],
  },
  { path: 'historial', component: HistorialComponent, canActivate: [authGuard] },
  { path: 'reporte', component: ReporteComponent, canActivate: [authGuard, permisoGuard('reportes')] },
  { path: '', redirectTo: 'carros', pathMatch: 'full' },
];
