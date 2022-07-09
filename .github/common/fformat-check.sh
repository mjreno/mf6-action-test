#! /bin/bash

#SEARCHPATHS=(src srcbmi utils)
SEARCHPATHS=(src)
FFORMATFAILS=()
EXCLUDEDIRS=(src/Utilities/Libraries/blas
             src/Utilities/Libraries/daglib
             src/Utilities/Libraries/rcm
             src/Utilities/Libraries/sparsekit
             src/Utilities/Libraries/sparskit2)
EXCLUDEFILES=(src/Utilities/InputOutput.f90)
checkcount=0
failcount=0

for path in "${SEARCHPATHS[@]}"
do
    mapfile -d '' files < <(find "${path}" -type f -print0 | grep -z '\.[fF][0-9+]')
    for file in "${files[@]}"
    do
        exclude=0

        for p in "${EXCLUDEDIRS[@]}"; 
        do [[ "${p}" == $(dirname "${file}") ]] && exclude=1 && break; done
        if [[ ${exclude} == 1 ]]; then continue; fi

        for f in "${EXCLUDEFILES[@]}";
        do [[ "${f}" == "${file}" ]] && exclude=1 && break; done;
        if [[ ${exclude} == 1 ]]; then continue; fi

        ((checkcount++))

        if [[ ! -z $(fprettify -d -c distribution/.fprettify.yaml "${file}" 2>&1) ]]; then
            FFORMATFAILS+=("${file}")
            ((failcount++))
        fi
    done
done

echo -e "\nFortran source files checked: ${checkcount}"
echo -e "Fortran source files failed: ${failcount}\n"
if [[ ${#FFORMATFAILS[@]} > 0 ]]; then
    for f in "${FFORMATFAILS[@]}"; do echo "${f}"; done
    echo -e "\nTo verify file format diff in local environment run:"
    echo -e "  'fprettify -d -c <path to modflow6>/distribution/.fprettify.yaml <filepath>'\n\n"
    exit 1
fi

exit 0
