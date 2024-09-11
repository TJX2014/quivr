import { useEffect, useState } from "react";

import { SyncElements } from "@/lib/api/sync/types";
import { useSync } from "@/lib/api/sync/useSync";
import { Icon } from "@/lib/components/ui/Icon/Icon";
import { LoaderIcon } from "@/lib/components/ui/LoaderIcon/LoaderIcon";

import styles from "./CurrentFolderExplorer.module.scss";
import CurrentFolderExplorerLine from "./CurrentFolderExplorerLine/CurrentFolderExplorerLine";

import { useKnowledgeContext } from "../KnowledgeProvider/hooks/useKnowledgeContext";

const CurrentFolderExplorer = (): JSX.Element => {
  const [loading, setLoading] = useState(false);
  const [syncElements, setSyncElements] = useState<SyncElements>();
  const { currentFolder } = useKnowledgeContext();
  const { getSyncFiles } = useSync();

  useEffect(() => {
    setLoading(true);
    void (async () => {
      try {
        if (currentFolder?.syncId) {
          const res = await getSyncFiles(
            currentFolder.syncId,
            currentFolder.id
          );
          setSyncElements((prevState) => ({
            ...prevState,
            files: res.files.map((syncElement) => ({
              ...syncElement,
              syncId: currentFolder.syncId,
            })),
          }));
        }
      } catch (error) {
        console.error("Failed to get sync files:", error);
      } finally {
        setLoading(false);
      }
    })();
  }, [currentFolder]);

  return (
    <div className={styles.current_folder_explorer_container}>
      <div className={styles.current_folder_explorer_wrapper}>
        <div className={styles.header}>
          {currentFolder?.icon ? (
            <div className={styles.icon}>{currentFolder.icon}</div>
          ) : (
            <Icon name={"folder"} color="black" size="normal" />
          )}
          <span>{currentFolder?.name?.replace(/(\..+)$/, "")}</span>
        </div>
        <div className={styles.current_folder_content}>
          {loading ? (
            <div className={styles.loading_icon}>
              <LoaderIcon size="large" color="primary" />
            </div>
          ) : (
            syncElements?.files
              .sort((a, b) => Number(b.is_folder) - Number(a.is_folder))
              .map((syncElement, index) => (
                <div key={index}>
                  <CurrentFolderExplorerLine element={syncElement} />
                </div>
              ))
          )}
        </div>
      </div>
    </div>
  );
};

export default CurrentFolderExplorer;