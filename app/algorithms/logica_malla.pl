% ==============================================================
% SISTEMA DE RECOMENDACIÓN ACADÉMICA CON PROLOG
% ==============================================================

% --- REGLAS DE DISPONIBILIDAD ---
% Un curso está disponible si cumple con sus prerrequisitos
curso_disponible(Codigo) :-
    curso(Codigo, _, _, _, Prereqs),
    \+ aprobado(Codigo),
    forall(member(P, Prereqs), aprobado(P)).

% --- ANÁLISIS DE CICLO ---
% Encuentra el último ciclo completado por el estudiante
encontrar_ultimo_ciclo_completo(UltimoCiclo) :-
    findall(C, (curso(_, _, C, _, _), C =< 10), CiclosPosibles),
    sort(CiclosPosibles, CiclosOrdenados),
    encontrar_ciclo_aux(CiclosOrdenados, 0, UltimoCiclo).

encontrar_ciclo_aux([], UltimoCompleto, UltimoCompleto).
encontrar_ciclo_aux([Ciclo|Resto], Anterior, UltimoCiclo) :-
    (   ciclo_completo(Ciclo)
    ->  encontrar_ciclo_aux(Resto, Ciclo, UltimoCiclo)
    ;   UltimoCiclo = Anterior
    ).

% Verifica si todos los cursos de un ciclo están aprobados
ciclo_completo(Ciclo) :-
    findall(C, curso(C, _, Ciclo, _, _), CursosCiclo),
    CursosCiclo \= [],
    forall(member(C, CursosCiclo), aprobado(C)).

% --- IDENTIFICACIÓN DE CURSOS PENDIENTES ---
% Encuentra cursos pendientes en un ciclo específico
cursos_pendientes_en_ciclo(Ciclo, CursosPendientes) :-
    findall(C, 
        (curso(C, _, Ciclo, _, _), \+ aprobado(C)),
        CursosPendientes
    ).

% --- CÁLCULO DE CRÉDITOS ---
% Calcula créditos totales de una lista de cursos
creditos_totales([], 0).
creditos_totales([Curso|Resto], Total) :-
    curso(Curso, _, _, Creditos, _),
    creditos_totales(Resto, SubTotal),
    Total is Creditos + SubTotal.

% --- SELECCIÓN DE CURSOS ---
% Selecciona cursos hasta alcanzar el límite de créditos
seleccionar_cursos([], _, [], 0).
seleccionar_cursos([Curso|Resto], MaxCreditos, [Curso|Seleccion], CreditosAcum) :-
    curso(Curso, _, _, Creditos, _),
    Creditos =< MaxCreditos,
    NuevoMax is MaxCreditos - Creditos,
    seleccionar_cursos(Resto, NuevoMax, Seleccion, SubCreditos),
    CreditosAcum is Creditos + SubCreditos.
seleccionar_cursos([_|Resto], MaxCreditos, Seleccion, CreditosAcum) :-
    seleccionar_cursos(Resto, MaxCreditos, Seleccion, CreditosAcum).

% --- PRIORIZACIÓN DE CURSOS ---
% Calcula cuántos cursos tienen a este curso como prerrequisito
es_prerrequisito_de_cuantos(Curso, Cantidad) :-
    findall(1, (curso(_, _, _, _, Prereqs), member(Curso, Prereqs)), Lista),
    length(Lista, Cantidad).

% Ordena cursos por prioridad (ciclo y prerrequisito)
ordenar_por_prioridad(Cursos, CursosOrdenados) :-
    maplist(calcular_prioridad, Cursos, CursosConPrioridad),
    sort(2, @>=, CursosConPrioridad, Ordenados),
    maplist(extraer_curso, Ordenados, CursosOrdenados).

calcular_prioridad(Curso, [Curso, Prioridad]) :-
    curso(Curso, _, Ciclo, _, _),
    es_prerrequisito_de_cuantos(Curso, CantidadPrereq),
    Prioridad is (11 - Ciclo) * 10 + CantidadPrereq.

extraer_curso([Curso, _], Curso).

% --- RECOMENDACIÓN PRINCIPAL ---
% Genera la recomendación completa de matrícula
recomendar_cursos(Recomendacion) :-
    encontrar_ultimo_ciclo_completo(UltimoCiclo),
    CicloMatricula is UltimoCiclo + 1,
    creditos_maximos(CicloMatricula, MaxCreditos),
    
    % Primero: cursos pendientes (obligatorios)
    cursos_pendientes_en_ciclo(CicloMatricula, CursosPendientes),
    seleccionar_cursos(CursosPendientes, MaxCreditos, PendientesSeleccionados, CreditosPendientes),
    
    % Segundo: cursos de avance disponibles
    findall(C, (curso_disponible(C), \+ member(C, CursosPendientes)), CursosAvance),
    ordenar_por_prioridad(CursosAvance, AvancePriorizados),
    CreditosRestantes is MaxCreditos - CreditosPendientes,
    seleccionar_cursos(AvancePriorizados, CreditosRestantes, AvanceSeleccionados, _),
    
    % Combinar ambas listas
    append(PendientesSeleccionados, AvanceSeleccionados, Recomendacion).

% --- VERIFICACIÓN DE ESTADO ACADÉMICO ---
% Determina si el estudiante está regular o irregular
estado_academico(regular) :-
    encontrar_ultimo_ciclo_completo(UltimoCiclo),
    CicloSiguiente is UltimoCiclo + 1,
    cursos_pendientes_en_ciclo(CicloSiguiente, []),
    !.
estado_academico(irregular).

% --- ANÁLISIS DE PROGRESO ---
% Calcula el porcentaje de avance en la carrera
porcentaje_avance(Porcentaje) :-
    findall(1, curso(_, _, _, _, _), TodosCursos),
    findall(1, aprobado(_), CursosAprobados),
    length(TodosCursos, Total),
    length(CursosAprobados, Aprobados),
    Total > 0,
    Porcentaje is (Aprobados * 100) // Total.

% --- PREDICCIÓN DE GRADUACIÓN ---
% Estima ciclos restantes para graduarse
ciclos_para_graduarse(CiclosRestantes) :-
    encontrar_ultimo_ciclo_completo(UltimoCiclo),
    findall(C, (curso(C, _, _, _, _), \+ aprobado(C)), CursosPendientes),
    length(CursosPendientes, CantidadPendientes),
    CantidadPendientes > 0,
    CiclosRestantes is (CantidadPendientes + 5) // 6.  % Promedio ~6 cursos por ciclo
ciclos_para_graduarse(0) :-
    encontrar_ultimo_ciclo_completo(10).
