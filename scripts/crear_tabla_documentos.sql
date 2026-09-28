-- Ejecutar una sola vez en Supabase > SQL Editor
create table if not exists public.documentos_transferencia (
    ppu            text primary key,
    url_solicitud  text,
    url_reingreso  text,
    url_padron     text,
    fecha_padron   date,
    actualizado_en timestamptz default now()
);

-- Si la tabla "transferencias" tiene RLS activado, replicar aquí sus mismas políticas (lectura, inserción y borrado).
-- Ejemplo (lectura para la llave del chat):
-- alter table public.documentos_transferencia enable row level security;
-- create policy "lectura chat" on public.documentos_transferencia for select using (true);
