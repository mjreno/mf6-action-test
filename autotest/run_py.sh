#! /bin/bash

SEARCHPATHS=(.)

fails=()
checkcount=0

for path in "${SEARCHPATHS[@]}"; do
  readarray -d '' files < <(find "${path}" -type f -print0 | grep -z 'test_gw.*\.py$')
  for file in "${files[@]}"; do
    #echo "${file}"
    time pytest "${file}"
    retVal=$?
    if [ $retVal -ne 0 ]; then
        fails+=("${file}")
    fi

    ((checkcount++))

  done
done

echo -e "\nFortran source files checked: ${checkcount}"
echo -e "fails: ${#fails[@]}\n"
if [[ ${#fails[@]} > 0 ]]; then
  for f in "${fails[@]}"; do echo "${f}"; done
fi
exit 0
