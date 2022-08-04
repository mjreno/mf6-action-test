#! /bin/bash

SEARCHPATHS=(.)

fails=()
checkcount=0

for path in "${SEARCHPATHS[@]}"; do
  #readarray -d '' files < <(find "${path}" -type f -print0 | grep -z 'test_gwf_[a-n].*\.py$')
  readarray -d '' files < <(find "${path}" -type f -print0 | grep -z 'test_.*\.py$')
  for file in "${files[@]}"; do
    #echo "${file}"
    #sed -i 's/msg = \"modflow_devtools not in PYTHONPATH\"/msg = \"modflow-devtools not in PYTHONPATH\"/g' "${file}"
    sed -i 's/\"autotest\",/\"autotest-keep\", \"standalone\",/g' "${file}"

    ((checkcount++))

  done
done

echo -e "\nFortran source files checked: ${checkcount}"
echo -e "fails: ${#fails[@]}\n"
if [[ ${#fails[@]} > 0 ]]; then
  for f in "${fails[@]}"; do echo "${f}"; done
fi
exit 0
