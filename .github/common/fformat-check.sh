#! /bin/bash

#SEARCHPATHS=(src srcbmi utils)
SEARCHPATHS=(src)
FCHECKFAILS=()

for path in "${SEARCHPATHS[@]}"
do
    echo "path=$path"
    mapfile -d '' files < <(find "$path" -type f -print0 | grep -z '\.[fF][0-9+]')
    for file in "${files[@]}"
    do
        if [[ ! -z $(fprettify -d -c distribution/.fprettify.yaml "$file" 2>/dev/null) ]]; then
            FCHECKFAILS+=("$file")
        fi
    done
done
echo "file checks complete"

if [[ ${#FCHECKFAILS[@]} > 0 ]]; then
    echo "Files failing formatting check:"
    for f in "${FCHECKFAILS[@]}"
    do
        echo "$f"
    done
    echo -e "\nTo verify file format diff in local environment run:"
    echo "  'fprettify -d -c <path to modflow6>/distribution/.fprettify.yaml <filepath>'"
    exit 1
fi

exit 0
