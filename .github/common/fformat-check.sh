#! /bin/bash

#SEARCHPATHS=(src srcbmi utils)
SEARCHPATHS=(src)
FCHECKFAILS=()

for path in "${SEARCHPATHS[@]}"
do
    mapfile -d '' files < <(find "$path" -type f -print0 | grep -z '\.[fF][0-9+]')
    for file in "${files[@]}"
    do
        if [[ ! -z $(fprettify -d -c ../modflow6/distribution/.fprettify.yaml "$file" 2>/dev/null) ]]; then
            FCHECKFAILS+=("$file")
        fi
    done
done

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
