#! /bin/bash

#SEARCHPATHS=(src srcbmi utils)
SEARCHPATHS=(src)
FCHECKFAILS=()

EXCLUDEDIRS=(src/Utilities/Libraries/blas
             src/Utilities/Libraries/daglib
             src/Utilities/Libraries/rcm
             src/Utilities/Libraries/sparsekit
             src/Utilities/Libraries/sparskit2)
EXCLUDEFILES=(src/Utilities/InputOutput.f90)

for path in "${SEARCHPATHS[@]}"
do
    mapfile -d '' files < <(find "$path" -type f -print0 | grep -z '\.[fF][0-9+]')
    for file in "${files[@]}"
    do
        if [[ ! "${EXCLUDEDIRS[*]}" =~ $(dirname "$file") ]] &&
           [[ ! "${EXCLUDEFILES[*]}" =~ "${file}" ]] &&
           [[ ! -z $(fprettify -d -c distribution/.fprettify.yaml "$file" 2>/dev/null) ]]; then
            FCHECKFAILS+=("$file")
        fi
    done
done

if [[ ${#FCHECKFAILS[@]} > 0 ]]; then
    echo -e "\n\nFiles failing formatting check:\n"
    for f in "${FCHECKFAILS[@]}"
    do
        echo "$f"
    done
    echo -e "\nTo verify file format diff in local environment run:"
    echo -e "  'fprettify -d -c <path to modflow6>/distribution/.fprettify.yaml <filepath>'\n\n"
    exit 1
fi

exit 0
