-- Ejecutar esto en el SQL Editor de Supabase antes de desplegar

-- Últimos precios conocidos por item + ciudad (se sobrescribe en cada cron)
create table if not exists precios_actuales (
  item_id text not null,
  city text not null,
  sell_price_min numeric,
  sell_price_min_date timestamptz,
  buy_price_max numeric,
  buy_price_max_date timestamptz,
  fetched_at timestamptz default now(),
  primary key (item_id, city)
);

-- Historial de mejor margen por item, uno por corrida del cron (crece con el tiempo)
create table if not exists margenes_historico (
  id bigserial primary key,
  item_id text not null,
  item_name text not null,
  origin text not null,
  dest text not null,
  margin numeric not null,
  margin_pct numeric not null,
  ts timestamptz default now()
);

-- Eventos económicos (parches, expansiones, cambios de profesión)
create table if not exists eventos_economia (
  id bigserial primary key,
  fecha date not null,
  titulo text not null,
  tipo text not null,       -- parche | expansion | profesion | evento
  impacto text not null,    -- alto | medio | bajo
  notas text,
  created_at timestamptz default now()
);

-- Configuración (fila única, id siempre 1)
create table if not exists config_usuario (
  id int primary key default 1,
  servidor text default 'west',
  impuesto numeric default 4,
  margen_minimo numeric default 200,
  max_antiguedad_horas numeric default 12,
  riesgo_ciudades jsonb default '{"Caerleon":75,"Bridgewatch":25,"Martlock":25,"Lymhurst":25,"FortSterling":25,"Thetford":25,"Brecilien":55}'::jsonb
);

insert into config_usuario (id) values (1) on conflict (id) do nothing;

-- Datos semilla de eventos (los mismos que traía la versión anterior)
insert into eventos_economia (fecha, titulo, tipo, impacto, notas) values
  ('2026-04-13', 'Radiant Wilds — actualización mayor', 'expansion', 'bajo',
   'Overhaul visual del mundo abierto, sistema de Armory y arenas PvP. Confirmado que no toca crafteo, refinado, impuestos ni tasas de retorno.'),
  ('2026-07-03', 'Keeper Uprising — evento con facción Ashborn', 'evento', 'medio',
   'Nuevos encuentros de mundo e invasiones de mazmorras estáticas. Puede mover la demanda de consumibles y materiales durante el evento (hasta el 31 de agosto).'),
  ('2026-07-04', 'Temporada 33 — ajustes a territorios y hideouts', 'parche', 'medio',
   'Cambios en puntos de territorio, costos y durabilidad de hideouts. Puede afectar demanda de materiales de construcción.')
on conflict do nothing;

-- Índices para que el historial y los eventos ordenen rápido
create index if not exists idx_margenes_item_ts on margenes_historico (item_id, ts desc);
create index if not exists idx_eventos_fecha on eventos_economia (fecha desc);
