"use client";

import { useEffect, useState } from "react";

import { Checkbox } from "@/lib/components/ui/Checkbox/Checkbox";
import { Icon } from "@/lib/components/ui/Icon/Icon";
import { QuivrButton } from "@/lib/components/ui/QuivrButton/QuivrButton";
import { TextInput } from "@/lib/components/ui/TextInput/TextInput";
import { filterAndSort, updateSelectedItems } from "@/lib/helpers/table";
import { useDevice } from "@/lib/hooks/useDevice";

import ProcessLine from "./Process/ProcessLine";
import styles from "./ProcessTab.module.scss";

import { Process } from "../types/process";

const mockProcesses: Process[] = [
  {
    id: 1,
    name: "Process 1",
    datetime: new Date().toISOString(),
    status: "pending",
  },
  {
    id: 2,
    name: "Process 2",
    datetime: new Date(Date.now() - 86400000 * 1).toISOString(),
    status: "processing",
  },
  {
    id: 3,
    name: "Process 3",
    datetime: new Date(Date.now() - 86400000 * 2).toISOString(),
    status: "completed",
  },
  {
    id: 4,
    name: "Process 4",
    datetime: new Date(Date.now() - 86400000 * 3).toISOString(),
    status: "error",
  },
  {
    id: 5,
    name: "Process 5",
    datetime: new Date(Date.now() - 86400000 * 4).toISOString(),
    status: "pending",
  },
  {
    id: 6,
    name: "Process 6",
    datetime: new Date(Date.now() - 86400000 * 5).toISOString(),
    status: "processing",
  },
  {
    id: 7,
    name: "Process 7",
    datetime: new Date(Date.now() - 86400000 * 6).toISOString(),
    status: "completed",
  },
];

const ProcessTab = (): JSX.Element => {
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedProcess, setSelectedProcess] = useState<Process[]>([]);
  const [allChecked, setAllChecked] = useState<boolean>(false);
  const [sortConfig, setSortConfig] = useState<{
    key: keyof Process;
    direction: "ascending" | "descending";
  }>({ key: "name", direction: "ascending" });
  const [filteredProcess, setFilteredProcess] =
    useState<Process[]>(mockProcesses);
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(
    null
  );

  const { isMobile } = useDevice();

  useEffect(() => {
    setFilteredProcess(
      filterAndSort(
        mockProcesses,
        searchQuery,
        sortConfig,
        (process) => process[sortConfig.key]
      )
    );
  }, [searchQuery, sortConfig]);

  const handleDelete = () => {
    console.info("delete");
  };

  const handleSelect = (
    process: Process,
    index: number,
    event: React.MouseEvent
  ) => {
    const newSelectedProcess = updateSelectedItems<Process>({
      item: process,
      index,
      event,
      lastSelectedIndex,
      filteredList: filteredProcess,
      selectedItems: selectedProcess,
    });
    setSelectedProcess(newSelectedProcess.selectedItems);
    setLastSelectedIndex(newSelectedProcess.lastSelectedIndex);
  };

  const handleSort = (key: keyof Process) => {
    setSortConfig((prevSortConfig) => {
      let direction: "ascending" | "descending" = "ascending";
      if (
        prevSortConfig.key === key &&
        prevSortConfig.direction === "ascending"
      ) {
        direction = "descending";
      }

      return { key, direction };
    });
  };

  return (
    <div className={styles.process_tab_wrapper}>
      <span className={styles.title}>Mes Résultats</span>
      <div className={styles.table_header}>
        <div className={styles.search}>
          <TextInput
            iconName="search"
            label="Search"
            inputValue={searchQuery}
            setInputValue={setSearchQuery}
            small={true}
          />
        </div>
        <QuivrButton
          label="Delete"
          iconName="delete"
          color="dangerous"
          disabled={selectedProcess.length === 0}
          onClick={handleDelete}
        />
      </div>
      <div>
        <div className={styles.first_line}>
          <div className={styles.left}>
            <Checkbox
              checked={allChecked}
              setChecked={(checked) => {
                setAllChecked(checked);
                setSelectedProcess(checked ? filteredProcess : []);
              }}
            />
            <div className={styles.name} onClick={() => handleSort("name")}>
              Nom
              <div className={styles.icon}>
                <Icon name="sort" size="small" color="black" />
              </div>
            </div>
          </div>
          <div className={styles.right}>
            {!isMobile && (
              <>
                <div
                  className={styles.date}
                  onClick={() => handleSort("datetime")}
                >
                  Date
                  <div className={styles.icon}>
                    <Icon name="sort" size="small" color="black" />
                  </div>
                </div>
                <div
                  className={styles.status}
                  onClick={() => handleSort("status")}
                >
                  Statut
                  <div className={styles.icon}>
                    <Icon name="sort" size="small" color="black" />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
        <div className={styles.process_list}>
          {filteredProcess.map((process, index) => (
            <div key={process.id} className={styles.process_line}>
              <ProcessLine
                process={process}
                last={index === filteredProcess.length - 1}
                selected={selectedProcess.some(
                  (item) => item.id === process.id
                )}
                setSelected={(_selected, event) =>
                  handleSelect(process, index, event)
                }
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProcessTab;
