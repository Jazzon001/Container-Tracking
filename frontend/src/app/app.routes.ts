import { Routes } from '@angular/router';
import { authGuard, rolGuard } from './auth.guard';
import { CargaComponent } from './carga.component';
import { CarrosComponent } from './carros.component';
import { EntregaComponent } from './entrega.component';
import { HistorialComponent } from './historial.component';
import { LoginComponent } from './login.component';
import { MantenimientoComponent } from './mantenimiento.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'carros', component: CarrosComponent, canActivate: [authGuard] },
  { path: 'carga', component: CargaComponent, canActivate: [authGuard, rolGuard('poy')] },
  { path: 'entrega', component: EntregaComponent, canActivate: [authGuard, rolGuard('almacen')] },
  {
    path: 'mantenimiento',
    component: MantenimientoComponent,
    canActivate: [authGuard, rolGuard('poy', 'dty')],
  },
  { path: 'historial', component: HistorialComponent, canActivate: [authGuard] },
  { path: '', redirectTo: 'carros', pathMatch: 'full' },
];
