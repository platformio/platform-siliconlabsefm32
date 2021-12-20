{# Helper macros to extract build information and tidy up its representation to a valid JSON -#}
{% macro normalize_path(path) -%}
    "{{ path | replace('-I"', '') | replace(' ', '\\ ') | replace('"','') | replace('$(SDK_PATH)', SDK_PATH) | replace('$(COPIED_SDK_PATH)', COPIED_SDK_PATH) | replace('\\', '\\\\') }}"
{%- endmacro -%}
{%- macro populate_flags(scope) -%}
    {%- for flag in scope %}
            "{{ flag | replace('"', '\\"') | replace('$(OUTPUT_DIR)', '$BUILD_DIR') | replace('$(PROJECTNAME)', PROJECT_NAME) | replace("\'", '') }}"{{ ',' if not loop.last }}
    {%- endfor %}
{%- endmacro -%}
{# TEMPLATE START -#}
{
    "flags": {
        "CFLAGS": [
            {{ populate_flags (EXT_CFLAGS) }}
        ],
        "CXXFLAGS": [
            {{ populate_flags (EXT_CXX_FLAGS) }}
        ],
        "ASFLAGS": [
            {{ populate_flags (EXT_ASM_FLAGS) }}
        ],
        "LINKFLAGS": [
            {{ populate_flags (EXT_LD_FLAGS) }}
        ]
    },
    "defines": {
        "ASDEFINES": [
            {{ populate_flags (ASM_DEFINE_STR) }}
        ],
        "CPPDEFINES": [
            {{ populate_flags (C_CXX_DEFINE_STR) }}
        ]
    },
    "includes": {
        "CPPPATH": [
            {%- for include in C_CXX_INCLUDES %}
            {{ normalize_path(include) }}{{ ',' if not loop.last }}
            {%- endfor %}
        ],
        "ASPATH": [
            {%- for include in ASM_INCLUDES %}
            {{ normalize_path(include) }}{{ ',' if not loop.last }}
            {%- endfor %}
        ]
    },
    "libraries": {
        "system": [
            {%- for lib in SYS_LIBS %}
            "{{ lib }}" {{',' if not loop.last }}
            {%- endfor %}
        ],
        "user": [
            {%- for lib in USER_LIBS %}
            {{ normalize_path(lib) }}{{ ',' if not loop.last }}
            {%- endfor %}
        ]
    },
    "sources": [
        {%- for source in (ALL_SOURCES | reject("none")) if source.endswith(('.c', '.cpp', '.cxx', '.cc', '.s', '.S')) %}
        {{ normalize_path(source) }}{{ ',' if not loop.last }}
        {%- endfor %}
    ],
    "dummy": "# SIMPLICITY_STUDIO_METADATA={{SIMPLICITY_STUDIO_METADATA}}=END_SIMPLICITY_STUDIO_METADATA"
}
