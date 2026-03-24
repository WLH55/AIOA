/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.repository;

import com.aiwork.helper.entity.Department;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 部门数据访问接口
 * 对应Go版本: internal/model/departmentmodel.go
 */
@Repository
public interface DepartmentRepository extends MongoRepository<Department, String> {

    /**
     * 根据部门名称查找
     */
    Department findByName(String name);

    /**
     * 根据ID列表批量查询部门
     */
    List<Department> findByIdIn(List<String> ids);

    /**
     * 根据父部门ID查找子部门列表
     */
    List<Department> findByParentId(String parentId);

    /**
     * 根据部门层级查找
     */
    List<Department> findByLevel(Integer level);

    /**
     * 根据负责人ID查找部门
     */
    List<Department> findByLeaderId(String leaderId);

    /**
     * 查找所有根部门 (没有父部门的部门)
     */
    @Query("{'parentId': {$exists: false}}")
    List<Department> findRootDepartments();

    /**
     * 根据父路径模糊查找 (查找某部门的所有子部门)
     * 对应Go: 解析parentPath进行查询
     */
    @Query("{'parentPath': {$regex: ?0}}")
    List<Department> findByParentPathContaining(String parentPath);
}